from datetime import datetime, timezone
from dataclasses import dataclass, asdict, field
import csv

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from dateutil import tz
from dateutil import parser

from .models import MemoText
from .forms import CSVUploadForm

JST = tz.gettz("Asia/Tokyo")

MIN_WIDTH = 10
MIN_ROWS = 10
SEARCH_WORD_MAX = 128

SELECTED = "selected"


@dataclass
class SearchMemoTextOption:
    title: str = ""
    label: str = ""
    memotext: str = ""


@dataclass
class SortMemoTextOption:
    id: str = ""
    title: str = ""
    label: str = ""
    update: str = ""


@dataclass
class MemoListContext:
    webmemo_list: any = None
    search_word: str = ""
    cate: SearchMemoTextOption = field(default_factory=SearchMemoTextOption)
    sorttype: SortMemoTextOption = field(default_factory=SortMemoTextOption)


def index(request):
    memolistcontext = MemoListContext()
    if request.method == "POST":
        addMemo(request)
        memolistcontext.webmemo_list = (
            MemoText.objects.all()
        )  # filter(owner=request.user)
    elif request.method == "GET":
        memolistcontext = filterMemoText(request)
    else:
        memolistcontext.webmemo_list = (
            MemoText.objects.all()
        )  # filter(owner=request.user)

    context = asdict(memolistcontext)
    return render(request, "webmemo/index.html", context)


def addMemo(request):
    try:
        if request.POST["webmemo_act"] == "add":
            MemoText.objects.create()
    except KeyError:
        return
    return


def searchMemoText(request) -> MemoListContext:
    memolistcontext = MemoListContext()
    if (
        not "cate" in request.GET
        or not "word" in request.GET
        or len(request.GET["word"]) == 0
        or len(request.GET["word"]) > SEARCH_WORD_MAX
    ):
        memolistcontext.webmemo_list = MemoText.objects.all()
        return memolistcontext
    memolistcontext.search_word = request.GET["word"]
    match request.GET["cate"]:
        case "title":
            memolistcontext.cate.title = SELECTED
            memolistcontext.webmemo_list = MemoText.objects.filter(
                titleName__icontains=request.GET["word"]
            )
        case "label":
            memolistcontext.cate.label = SELECTED
            memolistcontext.webmemo_list = MemoText.objects.filter(
                label__icontains=request.GET["word"]
            )

        case "memotext":
            memolistcontext.cate.memotext = SELECTED
            memolistcontext.webmemo_list = MemoText.objects.filter(
                mainText__icontains=request.GET["word"]
            )
        case _:
            memolistcontext.webmemo_list = MemoText.objects.all()
    return memolistcontext


def sortMemoText(request, memolistcontext: MemoListContext) -> MemoListContext:
    if not "sort" in request.GET:
        return memolistcontext
    if not memolistcontext.webmemo_list:
        memolistcontext.webmemo_list = MemoText.objects.all()
    match request.GET["sort"]:
        case "id":
            memolistcontext.sorttype.id = SELECTED
            memolistcontext.webmemo_list = memolistcontext.webmemo_list.order_by("id")
        case "title":
            memolistcontext.sorttype.title = SELECTED
            memolistcontext.webmemo_list = memolistcontext.webmemo_list.order_by(
                "titleName"
            )
        case "label":
            memolistcontext.sorttype.label = SELECTED
            memolistcontext.webmemo_list = memolistcontext.webmemo_list.order_by(
                "label"
            )
        case "update":
            memolistcontext.sorttype.update = SELECTED
            memolistcontext.webmemo_list = memolistcontext.webmemo_list.order_by(
                "-updated_at"
            )
        case _:
            pass
    return memolistcontext


def filterMemoText(request) -> MemoListContext:
    memolistcontext = searchMemoText(request=request)
    memolistcontext = sortMemoText(request=request, memolistcontext=memolistcontext)
    return memolistcontext


def edit(request, memo_id):
    if request.method == "POST":
        try:
            MemoText.objects.get(id=int(request.POST["memodeltextId"])).delete()
            return redirect(to="webmemo:index")
        except KeyError:
            update_msg = updateMemo(request, memo_id)

    memo = get_object_or_404(MemoText, id=memo_id)
    width = MIN_WIDTH
    rows = 0
    for text in memo.mainText.splitlines():
        if width < len(text):
            width = len(text)
        rows += 1
    width += 2  # margin
    rows += 2  # margin
    if rows < MIN_ROWS:
        rows = MIN_ROWS
    context = {"memo": memo, "width": width, "rows": rows}
    if "update_msg" in locals():
        context["update_msg"] = update_msg
    return render(request, "webmemo/edit.html", context)


def updateMemo(request, memo_id):
    try:
        edit_memo_id = int(request.POST["textId"])
        edit_memo_label = request.POST["label"]
        edit_memo_title = request.POST["titleName"]
        edit_memo_text = request.POST["maintext"]
    except KeyError:
        return ""
    else:
        if edit_memo_id != memo_id:
            return ""
        memo = get_object_or_404(MemoText, id=edit_memo_id)
        memo.label = edit_memo_label
        memo.titleName = edit_memo_title
        memo.mainText = edit_memo_text
        nowtime = datetime.now(timezone.utc)
        memo.updated_at = nowtime
        memo.save()
        return "更新しました : " + nowtime.astimezone(JST).isoformat()


def csv_download(request):
    # データベースから抽出したいデータを取得
    data = MemoText.objects.all()

    # CSVファイルの生成
    response = HttpResponse(content_type="text/csv")
    now = datetime.now(timezone.utc)
    response["Content-Disposition"] = f'attachment; filename="data_{now.date()}.csv"'

    writer = csv.writer(response)
    writer.writerow(
        ["id", "title", "label", "text", "updated_at", "created_at"]
    )  # ヘッダー行の書き込み

    for row in data:
        writer.writerow(
            [
                row.id,
                row.titleName,
                row.label,
                row.mainText,
                row.updated_at,
                row.created_at,
            ]
        )  # データ行の書き込み

    return response


def csv_upload(request):
    if request.method == "POST":
        # アップロードされたファイルを取得
        form = CSVUploadForm(request.POST, request.FILES)

        if form.is_valid():
            # CSVファイルの処理
            csv_file = request.FILES["csv_file"]
            csv_reader = csv.reader(csv_file.read().decode().splitlines())

            # ヘッダー行を除外
            next(csv_reader)

            # 各行を処理
            messages: list[str] = ["1行目　ヘッダーをスキップします。"]
            header_margin = 2
            add_data: dict[int, dict] = {}
            bad_data: dict[int, str] = {}
            for row_idx, row in enumerate(csv_reader):
                if len(row) == 5:
                    # データを生成
                    data = {
                        "titleName": row[0],
                        "label": row[1],
                        "mainText": row[2],
                        "created_at": parser.parse(row[3]),
                        "updated_at": parser.parse(row[4]),
                    }
                    add_data[row_idx + header_margin] = data
                    continue
                elif len(row) == 6:
                    data = {
                        "titleName": row[1],
                        "label": row[2],
                        "mainText": row[3],
                        "created_at": parser.parse(row[4]),
                        "updated_at": parser.parse(row[5]),
                    }
                    add_data[row_idx + header_margin] = data
                    continue
                else:
                    bad_data[row_idx + header_margin] = "フォーマットが違います。"
            if not bad_data:
                for idx, data in add_data.items():
                    # DBに保存
                    messages.append(
                        f"{idx}行目　{data['titleName']}, {data['label']}, を追加します。"
                    )
                    MemoText.objects.create(**data)
                if len(add_data):
                    messages.append("CSVファイルをアップロードしました。")
                else:
                    messages.append("有効なデータがありません。")
            else:
                for idx, data in bad_data.items():
                    messages.append(f"{idx}行目　{data}")
                messages.append("CSVファイルのアップロードを中止しました。")

            return render(
                request, "webmemo/csv_upload.html", {"form": form, "messages": messages}
            )
    else:
        # フォームを表示
        form = CSVUploadForm()

    return render(request, "webmemo/csv_upload.html", {"form": form})
