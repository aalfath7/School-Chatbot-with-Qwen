"""
Chatbot Sekolah berbasis Qwen.

Cara kerja: isi data-sekolah.txt dimasukkan ke system prompt, lalu Qwen
diminta menjawab HANYA berdasarkan data itu. Cocok untuk data kecil
(beberapa halaman). Kalau datanya sudah puluhan halaman, ganti ke RAG
(vector database) — lihat catatan di bawah.

Pakai API format OpenAI, jadi bisa jalan di dua tempat:
  1. Lokal lewat Ollama   -> gratis, data tidak keluar dari laptop
  2. Alibaba Cloud Model Studio (DashScope) -> berbayar, tapi model lebih besar

Install:  pip install openai
"""

import os
from pathlib import Path

from openai import APIConnectionError, NotFoundError, OpenAI

# ---------- PILIH BACKEND ----------
BACKEND = os.getenv("BACKEND", "ollama")  # "ollama" atau "dashscope"

if BACKEND == "ollama":
    client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    MODEL = os.getenv("MODEL", "qwen3.5:4b")  # laptop RAM 8 GB -> 4b; RAM 16 GB -> 8b
else:
    client = OpenAI(
        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        api_key=os.environ["DASHSCOPE_API_KEY"],
    )
    MODEL = os.getenv("MODEL", "qwen-plus")  # cek nama model terbaru di Model Studio

# ---------- MUAT DATA SEKOLAH ----------
# Path relatif ke folder skrip, jadi tetap jalan walau dipanggil dari folder lain
DATA_FILE = Path(__file__).parent / "data-sekolah.txt"
DATA = DATA_FILE.read_text(encoding="utf-8")

SYSTEM_PROMPT = f"""Kamu adalah asisten informasi resmi sekolah. Jawab dalam Bahasa Indonesia
yang sopan dan singkat, untuk orang tua, siswa, dan calon pendaftar.

ATURAN:
1. Jawab HANYA berdasarkan DATA SEKOLAH di bawah.
2. Jika informasinya tidak ada di data, katakan: "Maaf, informasi itu belum tersedia.
   Silakan hubungi TU sekolah." Jangan mengarang angka, tanggal, atau biaya.
3. Tolak dengan sopan pertanyaan di luar urusan sekolah.

DATA SEKOLAH:
{DATA}
"""


def tanya(riwayat: list) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + riwayat,
        temperature=0.2,  # rendah = jawaban lebih konsisten, tidak "kreatif"
        reasoning_effort="none",  # matikan mode berpikir -> jawaban lebih cepat
    )
    jawaban = resp.choices[0].message.content or ""
    # Qwen3 mode thinking kadang menyisipkan <think>...</think>; buang bagian itu
    if "</think>" in jawaban:
        jawaban = jawaban.split("</think>", 1)[1]
    return jawaban.strip()


def main():
    print(f"Chatbot Sekolah ({BACKEND}: {MODEL}). Ketik 'keluar' untuk berhenti.\n")
    riwayat = []
    while True:
        pesan = input("Anda: ").strip()
        if pesan.lower() in {"keluar", "exit", "quit"}:
            break
        if not pesan:
            continue
        # "/no_think" mematikan mode berpikir Qwen3 -> jawaban lebih cepat
        riwayat.append({"role": "user", "content": pesan})
        try:
            jawaban = tanya(riwayat[-10:])  # simpan 10 pesan terakhir saja
        except APIConnectionError:
            print("Error: tidak bisa terhubung ke Ollama. Pastikan Ollama sudah "
                  "terinstall dan berjalan (cek http://localhost:11434).")
            break
        except NotFoundError:
            print(f"Error: model '{MODEL}' belum diunduh. Jalankan: ollama pull {MODEL}")
            break
        riwayat.append({"role": "assistant", "content": jawaban})
        print(f"Bot: {jawaban}\n")


if __name__ == "__main__":
    main()