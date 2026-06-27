from fastapi import FastAPI, UploadFile, File
from paddleocr import PaddleOCR
import tempfile
import shutil
import re

app = FastAPI(title="NOTPUTRI OCR API")

ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False
)


def parse_ktp(text: str):
    data = {}

    nik = re.search(r"\b\d{16}\b", text)
    if nik:
        data["nik"] = nik.group()

    nama = re.search(r"Nama[:\s]+([A-Z ]+)", text, re.IGNORECASE)
    if nama:
        data["nama"] = nama.group(1).strip()

    ttl = re.search(
        r"Tempat/Tgl Lahir\s*[: ]+\s*([A-Z ]+),\s*(\d{2}-\d{2}-\d{4})",
        text,
        re.IGNORECASE,
    )
    if ttl:
        data["tempat_lahir"] = ttl.group(1).strip()
        data["tanggal_lahir"] = ttl.group(2)

    jk = re.search(r"Jenis Kelamin[: ]+([A-Z\-]+)", text, re.IGNORECASE)
    if jk:
        data["jenis_kelamin"] = jk.group(1).strip()

    pekerjaan = re.search(r"Pekerjaan[: ]+([A-Z ]+)", text, re.IGNORECASE)
    if pekerjaan:
        data["pekerjaan"] = pekerjaan.group(1).strip()

    agama = re.search(r"Agama[: ]+([A-Z]+)", text, re.IGNORECASE)
    if agama:
        data["agama"] = agama.group(1).strip()

    status = re.search(r"Status Perkawinan[: ]+([A-Z]+)", text, re.IGNORECASE)
    if status:
        data["status_perkawinan"] = status.group(1).strip()

    return data


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "NOTPUTRI OCR API"
    }


@app.post("/ocr")
async def scan_ktp(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    result = ocr.predict(tmp_path)

    text = []

    for page in result:
        if "rec_texts" in page:
            text.extend(page["rec_texts"])

    raw_text = "\n".join(text)

    parsed = parse_ktp(raw_text)

    return {
        "status": "success",
        "filename": file.filename,
        "raw_text": raw_text,
        "data": parsed
    }
