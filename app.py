"""
Tampilan web Chatbot Sekolah berbasis Gradio.

Logika chatbot tetap di chatbot.py; file ini hanya menambahkan tampilan chat.

Install:    pip install gradio openai
Jalankan:   python app.py
Lalu buka:  http://127.0.0.1:7860
"""

import gradio as gr
from openai import APIConnectionError, NotFoundError

from chatbot import BACKEND, MODEL, tanya


def ambil_teks(isi) -> str:
    # Gradio mengirim isi pesan lama sebagai daftar bagian: [{"type": "text", "text": "..."}]
    if isinstance(isi, str):
        return isi
    return "".join(bagian.get("text", "") for bagian in isi)


def balas(pesan: str, riwayat: list) -> str:
    pesan_lama = [
        {"role": m["role"], "content": ambil_teks(m["content"])} for m in riwayat
    ]
    try:
        # simpan 10 pesan terakhir saja, sama seperti versi terminal
        return tanya((pesan_lama + [{"role": "user", "content": pesan}])[-10:])
    except APIConnectionError:
        raise gr.Error("Tidak bisa terhubung ke Ollama. Pastikan Ollama sudah berjalan.")
    except NotFoundError:
        raise gr.Error(f"Model '{MODEL}' belum diunduh. Jalankan: ollama pull {MODEL}")


demo = gr.ChatInterface(
    balas,
    title="Chatbot Sekolah",
    description="Tanyakan informasi seputar sekolah, PPDB, biaya, dan program.",
    examples=[
        "Berapa SPP dan uang pangkal tahun ajaran 2027/2028?",
        "Apa syarat pendaftaran PPDB 2027/2028?",
        "Apakah calon siswa harus sudah hafal juz 30?",
        "Apa saja ekstrakurikuler pilihan yang tersedia?",
    ],
    cache_examples=False,
    analytics_enabled=False,  # jangan kirim data pemakaian ke Gradio
)

if __name__ == "__main__":
    print(f"Chatbot Sekolah ({BACKEND}: {MODEL})")
    demo.launch()
