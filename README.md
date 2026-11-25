# Tes Render Ruang Healing di Cloud (Colab / Kaggle)

**Tujuan:** membuktikan pipeline render stickman Ruang Healing (PIL + ffmpeg)
bisa jalan di mesin cloud yang RAM-nya jauh lebih besar dari VM Muse
(VM: ~8GB, Colab gratis: ~12GB, Kaggle gratis: ~30GB + GPU 2x T4).

**Isi repo:**
- `rh_stickman_lib.py` — library gambar stickman (sama seperti produksi)
- `render_rh31.py` — render Hari 31 penuh (sama seperti produksi, path dibuat portabel)
- `test_render_10s.py` — render 10 detik pertama Hari 31 (tes cepat) + ukur kecepatan + ffprobe
- `narasi.mp3`, `segments.json`, `scene_map.json` — aset Hari 31
- `music-bed.wav` — musik latar
- `test-colab.ipynb` — notebook siap jalan di Google Colab
- `test-kaggle.ipynb` — notebook siap jalan di Kaggle

**Cara tes di Colab:** buka https://colab.research.google.com/github/intan151/rh-render-test/blob/main/test-colab.ipynb → Runtime → Run all.

**Cara tes di Kaggle:** buat notebook baru → File → Import from GitHub (atau clone manual) → jalankan sel-sel `test-kaggle.ipynb`. Aktifkan Internet di panel kanan (butuh verifikasi nomor HP).

**Yang diukur:** video `test-hari31-10s.mp4` jadi (720x1280, 10 detik, ada suara narasi + musik) + kecepatan render (frame/detik). Kalau 10 detik ini jalan, video penuh tinggal `python3 render_rh31.py`.
