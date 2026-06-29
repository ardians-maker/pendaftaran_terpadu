import streamlit as st
import pandas as pd
import numpy as np
import pickle
import os

# Konfigurasi Halaman
st.set_page_config(page_title="Sistem Faskes Terpadu", page_icon="🏥", layout="wide")

# ==========================================
# 1. SETUP DATABASE (EXCEL)
# ==========================================
DB_PASIEN = 'db_pasien.xlsx'
DB_ANTRIAN = 'db_antrian.xlsx'
DB_DOKTER = 'db_dokter.xlsx'
DB_REKAM_MEDIS = 'db_rekam_medis.xlsx'

def init_db(file_name, columns):
    if not os.path.exists(file_name):
        pd.DataFrame(columns=columns).to_excel(file_name, index=False)

init_db(DB_PASIEN, ['ID', 'Nama', 'Face_Embedding'])
init_db(DB_ANTRIAN, ['ID_Antrian', 'Nama_Pasien', 'Faskes', 'Jenis', 'Poli', 'Status_Rujukan'])
init_db(DB_DOKTER, ['Username', 'Password', 'Faskes'])
init_db(DB_REKAM_MEDIS, ['Nama_Pasien', 'Faskes', 'Diagnosis', 'Rujukan_Tujuan'])

# ==========================================
# 2. LOAD MODEL PENDETEKSI WAJAH (.pkl)
# ==========================================
# Hapus tanda komentar di bawah ini jika file model_wajah.pkl sudah ada
"""
@st.cache_resource
def load_model():
    with open('model_wajah.pkl', 'rb') as file:
        return pickle.load(file)
face_model = load_model()
"""

def ekstrak_fitur_wajah(image_buffer):
    # TODO: Baca image_buffer menggunakan PIL atau cv2, lalu masukkan ke face_model.predict()
    # Contoh simulasi pengenalan wajah:
    return str(np.random.rand(128).tolist()) 

def verifikasi_wajah(image_buffer):
    df = pd.read_excel(DB_PASIEN)
    if df.empty:
        return False, "Belum ada pasien terdaftar."
    
    # TODO: Bandingkan fitur wajah dari input dengan 'Face_Embedding' di database
    # Simulasi return:
    return True, "Pasien Simulasi" 

# ==========================================
# 3. TAMPILAN ANTARMUKA (UI)
# ==========================================
st.title("🏥 Sistem Informasi Terpadu Faskes & Rujukan")

tab_pasien, tab_admin, tab_dokter = st.tabs(["🧑‍🤝‍🧑 Area Pasien", "⚙️ Administrasi Faskes", "👨‍⚕️ Area Dokter"])

# ---------------------------------
# TAB 1: PASIEN
# ---------------------------------
with tab_pasien:
    menu_pasien = st.radio("Pilih Menu:", ["Login & Ambil Antrian", "Daftar Akun Baru (Scan Wajah)"], horizontal=True)
    st.divider()

    if menu_pasien == "Daftar Akun Baru (Scan Wajah)":
        st.subheader("Pendaftaran Akun")
        nama_input = st.text_input("Nama Lengkap")
        cam_daftar = st.camera_input("Ambil Foto Wajah untuk Pendaftaran")
        
        if st.button("Daftar Akun", type="primary"):
            if cam_daftar is None or not nama_input:
                st.error("Gagal: Mohon isi nama dan ambil foto wajah.")
            else:
                fitur = ekstrak_fitur_wajah(cam_daftar)
                df = pd.read_excel(DB_PASIEN)
                new_data = pd.DataFrame({'ID': [len(df)+1], 'Nama': [nama_input], 'Face_Embedding': [fitur]})
                df = pd.concat([df, new_data], ignore_index=True)
                df.to_excel(DB_PASIEN, index=False)
                st.success(f"Berhasil: Pasien {nama_input} terdaftar. Silakan ke menu Login.")

    elif menu_pasien == "Login & Ambil Antrian":
        st.subheader("Login & Pengambilan Antrian")
        col1, col2 = st.columns(2)
        
        with col1:
            cam_login = st.camera_input("Scan Wajah untuk Login")
        
        with col2:
            faskes_pilih = st.selectbox("Pilih Faskes", ["Puskesmas A", "RSUD B", "RS Pusat C"])
            jenis_pasien = st.radio("Jenis Pasien", ["Biasa", "Rujukan"])
            layanan_pilih = st.selectbox("Pilih Layanan (Abaikan jika Rujukan)", ["Poli Umum", "Poli Gigi", "Poli Mata"])
            
            if st.button("Login & Ambil Antrian", type="primary"):
                if cam_login is None:
                    st.error("Mohon scan wajah terlebih dahulu.")
                else:
                    status, nama = verifikasi_wajah(cam_login)
                    if not status:
                        st.error("Login Gagal: Wajah tidak dikenali.")
                    else:
                        catatan_rujukan = ""
                        lanjut_antri = True
                        
                        if jenis_pasien == "Rujukan":
                            df_rm = pd.read_excel(DB_REKAM_MEDIS)
                            rujukan = df_rm[(df_rm['Nama_Pasien'] == nama) & (df_rm['Rujukan_Tujuan'] == faskes_pilih)]
                            if not rujukan.empty:
                                catatan_rujukan = " (Data Rujukan Terverifikasi)"
                                layanan_pilih = "Poli Rujukan Otomatis"
                            else:
                                st.error(f"Tidak ditemukan surat rujukan untuk {nama} ke {faskes_pilih}.")
                                lanjut_antri = False

                        if lanjut_antri:
                            df = pd.read_excel(DB_ANTRIAN)
                            no_antrian = len(df) + 1
                            new_data = pd.DataFrame({
                                'ID_Antrian': [no_antrian], 'Nama_Pasien': [nama], 
                                'Faskes': [faskes_pilih], 'Jenis': [jenis_pasien], 
                                'Poli': [layanan_pilih], 'Status_Rujukan': [catatan_rujukan]
                            })
                            df = pd.concat([df, new_data], ignore_index=True)
                            df.to_excel(DB_ANTRIAN, index=False)
                            
                            st.success(f"Login Berhasil! Selamat datang, {nama}.")
                            st.info(f"Nomor Antrian Anda: **{no_antrian}**\n\nFaskes: {faskes_pilih} | Layanan: {layanan_pilih} {catatan_rujukan}")

# ---------------------------------
# TAB 2: ADMIN FASKES
# ---------------------------------
with tab_admin:
    st.subheader("⚙️ Panel Administrasi")
    st.caption("Khusus Dinas/Lembaga Berwenang")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Daftarkan Dokter Baru**")
        with st.form("form_dokter"):
            u_dok = st.text_input("Username Dokter")
            p_dok = st.text_input("Password", type="password")
            f_dok = st.selectbox("Faskes Penempatan", ["Puskesmas A", "RSUD B", "RS Pusat C"])
            submit_dok = st.form_submit_button("Daftarkan Dokter")
            
            if submit_dok:
                df = pd.read_excel(DB_DOKTER)
                new_data = pd.DataFrame({'Username': [u_dok], 'Password': [p_dok], 'Faskes': [f_dok]})
                df = pd.concat([df, new_data], ignore_index=True)
                df.to_excel(DB_DOKTER, index=False)
                st.success(f"Dokter {u_dok} berhasil didaftarkan di {f_dok}.")
                
    with col2:
        st.markdown("**Pantau Antrian Faskes**")
        df_antri = pd.read_excel(DB_ANTRIAN)
        st.dataframe(df_antri, use_container_width=True)

# ---------------------------------
# TAB 3: DOKTER
# ---------------------------------
with tab_dokter:
    # Session state untuk menyimpan status login dokter
    if "dokter_logged_in" not in st.session_state:
        st.session_state.dokter_logged_in = False
        st.session_state.nama_dokter = ""
        st.session_state.faskes_dokter = ""

    if not st.session_state.dokter_logged_in:
        st.subheader("Login Dokter")
        with st.form("login_dokter"):
            u_login = st.text_input("Username")
            p_login = st.text_input("Password", type="password")
            btn_login_dok = st.form_submit_button("Login")
            
            if btn_login_dok:
                df_dok = pd.read_excel(DB_DOKTER)
                dok_match = df_dok[(df_dok['Username'] == u_login) & (df_dok['Password'] == p_login)]
                if not dok_match.empty:
                    st.session_state.dokter_logged_in = True
                    st.session_state.nama_dokter = u_login
                    st.session_state.faskes_dokter = dok_match['Faskes'].values[0]
                    st.rerun() # Refresh halaman
                else:
                    st.error("Username atau Password salah.")
    else:
        st.success(f"Berhasil login sebagai **dr. {st.session_state.nama_dokter}** ({st.session_state.faskes_dokter})")
        if st.button("Logout"):
            st.session_state.dokter_logged_in = False
            st.rerun()
            
        st.divider()
        st.subheader("Input Rekam Medis & Tindakan")
        
        with st.form("form_pemeriksaan"):
            pasien_nama = st.text_input("Nama Pasien yang Diperiksa")
            diagnosis = st.text_area("Catatan Rekam Medis / Diagnosis")
            status_tindakan = st.radio("Tindakan Lanjutan", ["Selesai", "Rujuk"])
            rs_rujuk = st.selectbox("Pilih RS Rujukan (Bila Perlu)", ["-", "RSUD B", "RS Pusat C"])
            
            btn_simpan_rm = st.form_submit_button("Simpan Sesi / Terbitkan Rujukan")
            
            if btn_simpan_rm:
                if not pasien_nama or not diagnosis:
                    st.warning("Mohon isi nama pasien dan diagnosis.")
                else:
                    tujuan = rs_rujuk if status_tindakan == "Rujuk" else "-"
                    df_rm = pd.read_excel(DB_REKAM_MEDIS)
                    new_data = pd.DataFrame({'Nama_Pasien': [pasien_nama], 'Faskes': [st.session_state.faskes_dokter], 'Diagnosis': [diagnosis], 'Rujukan_Tujuan': [tujuan]})
                    df_rm = pd.concat([df_rm, new_data], ignore_index=True)
                    df_rm.to_excel(DB_REKAM_MEDIS, index=False)
                    
                    st.success(f"Rekam medis {pasien_nama} berhasil disimpan.")
                    if status_tindakan == "Rujuk":
                        st.info(f"Pasien otomatis dirujuk ke {rs_rujuk}. Data terhubung otomatis.")
