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
DB_PASIEN = 'db_pasien_v2.xlsx'
DB_ANTRIAN = 'db_antrian_v2.xlsx'
DB_DOKTER = 'db_dokter_v2.xlsx'
DB_REKAM_MEDIS = 'db_rekam_medis_v2.xlsx'
DB_FASILITAS = 'db_fasilitas_v2.xlsx'

def init_db(file_name, columns):
    if not os.path.exists(file_name):
        pd.DataFrame(columns=columns).to_excel(file_name, index=False)

init_db(DB_PASIEN, ['ID', 'Nama', 'Alamat', 'Face_Embedding'])
init_db(DB_ANTRIAN, ['ID_Antrian', 'Nama_Pasien', 'Faskes', 'Jenis', 'Poli', 'Keluhan', 'Status_Rujukan', 'Status_Periksa'])
init_db(DB_DOKTER, ['Username', 'Password', 'Faskes'])
init_db(DB_REKAM_MEDIS, ['Nama_Pasien', 'Faskes', 'Diagnosis', 'Rujukan_Tujuan'])
init_db(DB_FASILITAS, ['Faskes', 'Kapasitas_Rawat_Inap', 'Terisi', 'Status_Penuh'])

# ==========================================
# 2. LOAD MODEL PENDETEKSI WAJAH (.pkl)
# ==========================================
"""
@st.cache_resource
def load_model():
    with open('model_wajah.pkl', 'rb') as file:
        return pickle.load(file)
face_model = load_model()
"""

def ekstrak_fitur_wajah(image_buffer):
    return str(np.random.rand(128).tolist()) 

def verifikasi_wajah(image_buffer):
    df = pd.read_excel(DB_PASIEN)
    if df.empty:
        return False, "", ""
    return True, df.iloc[0]['Nama'], df.iloc[0]['Alamat']

# ==========================================
# 3. INISIALISASI SESSION STATE
# ==========================================
if "pasien_verified" not in st.session_state:
    st.session_state.pasien_verified = False
    st.session_state.p_nama = ""
    st.session_state.p_alamat = ""

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
    st.session_state.admin_faskes = ""

if "dokter_logged_in" not in st.session_state:
    st.session_state.dokter_logged_in = False
    st.session_state.nama_dokter = ""
    st.session_state.faskes_dokter = ""

# ==========================================
# 4. TAMPILAN ANTARMUKA (UI)
# ==========================================
st.title("🏥 Sistem Informasi Terpadu Faskes & Rujukan")

tab_pasien, tab_admin, tab_dokter = st.tabs(["🧑‍🤝‍🧑 Area Pasien", "⚙️ Administrasi Faskes", "👨‍⚕️ Area Dokter"])

# ---------------------------------
# TAB 1: PASIEN
# ---------------------------------
with tab_pasien:
    with st.expander("📊 Lihat Informasi Ketersediaan Fasilitas Rawat Inap", expanded=False):
        df_fas_view = pd.read_excel(DB_FASILITAS)
        if not df_fas_view.empty:
            st.dataframe(df_fas_view, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data fasilitas yang diupdate.")

    menu_pasien = st.radio("Pilih Menu:", ["Login & Ambil Antrian", "Daftar Akun Baru (Scan Wajah)"], horizontal=True)
    st.divider()

    if menu_pasien == "Daftar Akun Baru (Scan Wajah)":
        st.subheader("Pendaftaran Akun")
        nama_input = st.text_input("Nama Lengkap")
        alamat_input = st.text_area("Alamat Lengkap")
        cam_daftar = st.camera_input("Ambil Foto Wajah untuk Pendaftaran")
        
        if st.button("Daftar Akun", type="primary"):
            if cam_daftar is None or not nama_input or not alamat_input:
                st.error("Gagal: Mohon isi nama, alamat, dan ambil foto wajah.")
            else:
                fitur = ekstrak_fitur_wajah(cam_daftar)
                df = pd.read_excel(DB_PASIEN)
                new_data = pd.DataFrame({'ID': [len(df)+1], 'Nama': [nama_input], 'Alamat': [alamat_input], 'Face_Embedding': [fitur]})
                df = pd.concat([df, new_data], ignore_index=True)
                df.to_excel(DB_PASIEN, index=False)
                st.success(f"Berhasil: Pasien {nama_input} terdaftar. Silakan ke menu Login.")

    elif menu_pasien == "Login & Ambil Antrian":
        if not st.session_state.pasien_verified:
            st.subheader("Langkah 1: Verifikasi Wajah")
            cam_login = st.camera_input("Scan Wajah untuk Login")
            if st.button("Verifikasi Wajah", type="primary"):
                if cam_login is None:
                    st.error("Mohon scan wajah terlebih dahulu.")
                else:
                    status, nama, alamat = verifikasi_wajah(cam_login)
                    if status:
                        st.session_state.pasien_verified = True
                        st.session_state.p_nama = nama
                        st.session_state.p_alamat = alamat
                        st.rerun()
                    else:
                        st.error("Login Gagal: Wajah tidak dikenali.")
        else:
            st.subheader("Langkah 2: Pengambilan Antrian")
            st.info(f"**Biodata Pasien:**\n\nNama: {st.session_state.p_nama}\n\nAlamat: {st.session_state.p_alamat}")
            
            faskes_pilih = st.selectbox("Pilih Faskes Tujuan", ["Puskesmas A", "RSUD B", "RS Pusat C"])
            jenis_pasien = st.radio("Jenis Pasien", ["Biasa", "Rujukan"])
            layanan_pilih = st.selectbox("Pilih Layanan (Abaikan jika Rujukan)", ["Poli Umum", "Poli Gigi", "Poli Mata"])
            keluhan_input = st.text_area("Keluhan Singkat (Opsional, untuk dibaca dokter)")
            
            if st.button("Ambil Antrian", type="primary"):
                catatan_rujukan = ""
                lanjut_antri = True
                
                if jenis_pasien == "Rujukan":
                    df_rm = pd.read_excel(DB_REKAM_MEDIS)
                    rujukan = df_rm[(df_rm['Nama_Pasien'] == st.session_state.p_nama) & (df_rm['Rujukan_Tujuan'] == faskes_pilih)]
                    
                    if not rujukan.empty:
                        data_terakhir = rujukan.iloc[-1]
                        faskes_asal = data_terakhir['Faskes']
                        diagnosis_asal = data_terakhir['Diagnosis']
                        catatan_rujukan = f"[RUJUKAN dari {faskes_asal}] - Rekam Medis: {diagnosis_asal}"
                        layanan_pilih = "Poli Rujukan Otomatis"
                        st.success(f"✅ Data Rujukan Ditemukan!\n\n**Faskes Asal:** {faskes_asal}\n**Diagnosis Sebelumnya:** {diagnosis_asal}")
                    else:
                        st.error(f"Tidak ditemukan surat rujukan untuk {st.session_state.p_nama} ke {faskes_pilih}.")
                        lanjut_antri = False

                if lanjut_antri:
                    df_antrian = pd.read_excel(DB_ANTRIAN)
                    antrian_sebelumnya = len(df_antrian[(df_antrian['Faskes'] == faskes_pilih) & 
                                                        (df_antrian['Poli'] == layanan_pilih) & 
                                                        (df_antrian['Status_Periksa'] == 'Belum')])
                    no_antrian = len(df_antrian) + 1
                    
                    new_data = pd.DataFrame({
                        'ID_Antrian': [no_antrian], 'Nama_Pasien': [st.session_state.p_nama], 
                        'Faskes': [faskes_pilih], 'Jenis': [jenis_pasien], 
                        'Poli': [layanan_pilih], 'Keluhan': [keluhan_input],
                        'Status_Rujukan': [catatan_rujukan], 'Status_Periksa': ['Belum']
                    })
                    df_antrian = pd.concat([df_antrian, new_data], ignore_index=True)
                    df_antrian.to_excel(DB_ANTRIAN, index=False)
                    
                    st.success(f"Antrian Berhasil Diambil!")
                    st.warning(f"🏥 **Nomor Antrian Anda: {no_antrian}**\n\nAnda harus menunggu **{antrian_sebelumnya} antrian lagi** sebelum giliran Anda.")
                    
                    if st.button("Selesai / Keluar"):
                        st.session_state.pasien_verified = False
                        st.rerun()

# ---------------------------------
# TAB 2: ADMIN FASKES
# ---------------------------------
with tab_admin:
    akun_admin = {
        "puskesmasA": {"pwd": "sehatceria123", "faskes": "Puskesmas A"},
        "RumahsakitB": {"pwd": "sehatceria123", "faskes": "RSUD B"}
    }

    if not st.session_state.admin_logged_in:
        st.subheader("Login Administrasi Faskes")
        u_admin = st.text_input("Username Admin")
        p_admin = st.text_input("Password Admin", type="password")
        
        if st.button("Login Admin"):
            if u_admin in akun_admin and p_admin == akun_admin[u_admin]["pwd"]:
                st.session_state.admin_logged_in = True
                st.session_state.admin_faskes = akun_admin[u_admin]["faskes"]
                st.rerun()
            else:
                st.error("Kredensial Admin Salah!")
    else:
        admin_faskes = st.session_state.admin_faskes
        st.subheader(f"⚙️ Panel Administrasi - {admin_faskes}")
        if st.button("Logout Admin"):
            st.session_state.admin_logged_in = False
            st.session_state.admin_faskes = ""
            st.rerun()
            
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**1. Daftarkan Dokter Baru**")
            with st.form("form_dokter"):
                u_dok = st.text_input("Username Dokter")
                p_dok = st.text_input("Password", type="password")
                st.text_input("Faskes Penempatan", value=admin_faskes, disabled=True)
                
                if st.form_submit_button("Daftarkan Dokter"):
                    df = pd.read_excel(DB_DOKTER)
                    new_data = pd.DataFrame({'Username': [u_dok], 'Password': [p_dok], 'Faskes': [admin_faskes]})
                    df = pd.concat([df, new_data], ignore_index=True)
                    df.to_excel(DB_DOKTER, index=False)
                    st.success(f"Dokter {u_dok} berhasil didaftarkan di {admin_faskes}.")
                    
            st.markdown("**2. Update Fasilitas Rawat Inap**")
            with st.form("form_fasilitas"):
                st.text_input("Faskes", value=admin_faskes, disabled=True)
                kapasitas = st.number_input("Total Kapasitas Bed", min_value=0)
                terisi = st.number_input("Bed Terisi", min_value=0)
                status_penuh = "Penuh" if terisi >= kapasitas else "Tersedia"
                
                if st.form_submit_button("Update Fasilitas"):
                    df_fasilitas = pd.read_excel(DB_FASILITAS)
                    df_fasilitas = df_fasilitas[df_fasilitas['Faskes'] != admin_faskes]
                    new_fasilitas = pd.DataFrame({'Faskes': [admin_faskes], 'Kapasitas_Rawat_Inap': [kapasitas], 'Terisi': [terisi], 'Status_Penuh': [status_penuh]})
                    df_fasilitas = pd.concat([df_fasilitas, new_fasilitas], ignore_index=True)
                    df_fasilitas.to_excel(DB_FASILITAS, index=False)
                    st.success(f"Fasilitas diupdate! Status: {status_penuh}")
                    
        with col2:
            st.markdown(f"**Pantau Antrian - {admin_faskes}**")
            df_antri = pd.read_excel(DB_ANTRIAN)
            df_antri_filter = df_antri[df_antri['Faskes'] == admin_faskes]
            st.dataframe(df_antri_filter, use_container_width=True, hide_index=True)
            
            st.markdown("**Status Fasilitas Saat Ini**")
            df_fas_view = pd.read_excel(DB_FASILITAS)
            df_fas_filter = df_fas_view[df_fas_view['Faskes'] == admin_faskes]
            st.dataframe(df_fas_filter, use_container_width=True, hide_index=True)

# ---------------------------------
# TAB 3: DOKTER
# ---------------------------------
with tab_dokter:
    if not st.session_state.dokter_logged_in:
        st.subheader("Login Dokter")
        with st.form("login_dokter"):
            u_login = st.text_input("Username")
            p_login = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                df_dok = pd.read_excel(DB_DOKTER)
                dok_match = df_dok[(df_dok['Username'] == u_login) & (df_dok['Password'] == p_login)]
                if not dok_match.empty:
                    st.session_state.dokter_logged_in = True
                    st.session_state.nama_dokter = u_login
                    st.session_state.faskes_dokter = dok_match['Faskes'].values[0]
                    st.rerun()
                else:
                    st.error("Username atau Password salah.")
    else:
        st.success(f"Berhasil login sebagai **dr. {st.session_state.nama_dokter}** ({st.session_state.faskes_dokter})")
        if st.button("Logout Dokter"):
            st.session_state.dokter_logged_in = False
            st.rerun()
            
        st.divider()
        st.subheader("Input Rekam Medis & Tindakan")
        
        df_antrian_dok = pd.read_excel(DB_ANTRIAN)
        pasien_tunggu = df_antrian_dok[(df_antrian_dok['Faskes'] == st.session_state.faskes_dokter) & (df_antrian_dok['Status_Periksa'] == 'Belum')]
        
        if pasien_tunggu.empty:
            st.info("Saat ini tidak ada antrian pasien.")
        else:
            pilih_pasien = st.selectbox("Pilih Pasien dari Antrian", pasien_tunggu['Nama_Pasien'].tolist())
            data_pilih = pasien_tunggu[pasien_tunggu['Nama_Pasien'] == pilih_pasien].iloc[0]
            
            # 1. PERBAIKAN: Bersihkan nilai 'nan' pada kolom keluhan
            keluhan_mentah = data_pilih['Keluhan']
            keluhan_bersih = "-" if pd.isna(keluhan_mentah) or str(keluhan_mentah).lower() == 'nan' or str(keluhan_mentah) == "" else str(keluhan_mentah)
            
            # 2. PERBAIKAN: Ambil riwayat rujukan langsung dari database rekam medis, bukan dari antrean
            df_rm_all = pd.read_excel(DB_REKAM_MEDIS)
            # Cek apakah ada data di mana pasien ini dirujuk ke faskes dokter yang sedang login
            riwayat_rujukan = df_rm_all[(df_rm_all['Nama_Pasien'] == pilih_pasien) & (df_rm_all['Rujukan_Tujuan'] == st.session_state.faskes_dokter)]
            
            if not riwayat_rujukan.empty:
                # Jika ada rujukan, ambil data yang paling terakhir
                data_rm_lama = riwayat_rujukan.iloc[-1]
                info_rm_sebelumnya = f"Rujukan dari: {data_rm_lama['Faskes']}\nDiagnosis Sebelumnya: {data_rm_lama['Diagnosis']}"
            else:
                info_rm_sebelumnya = "Bukan Pasien Rujukan / Tidak ada data riwayat rujukan ke faskes ini."
            
            colA, colB = st.columns(2)
            with colA:
                st.text_area("Keluhan Pasien (Dari Pendaftaran)", value=keluhan_bersih, disabled=True)
            with colB:
                st.text_area("Informasi Rujukan Sebelumnya", value=info_rm_sebelumnya, disabled=True)
            
            with st.form("form_pemeriksaan"):
                diagnosis = st.text_area("Catatan Rekam Medis / Diagnosis Baru")
                status_tindakan = st.radio("Tindakan Lanjutan", ["Selesai", "Rujuk"])
                rs_rujuk = st.selectbox("Pilih RS Rujukan (Bila Perlu)", ["-", "RSUD B", "RS Pusat C"])
                
                if st.form_submit_button("Simpan Sesi / Terbitkan Rujukan"):
                    if not diagnosis:
                        st.warning("Mohon isi diagnosis.")
                    else:
                        tujuan = rs_rujuk if status_tindakan == "Rujuk" else "-"
                        df_rm = pd.read_excel(DB_REKAM_MEDIS)
                        new_data = pd.DataFrame({'Nama_Pasien': [pilih_pasien], 'Faskes': [st.session_state.faskes_dokter], 'Diagnosis': [diagnosis], 'Rujukan_Tujuan': [tujuan]})
                        df_rm = pd.concat([df_rm, new_data], ignore_index=True)
                        df_rm.to_excel(DB_REKAM_MEDIS, index=False)
                        
                        idx_update = df_antrian_dok.index[(df_antrian_dok['Nama_Pasien'] == pilih_pasien) & (df_antrian_dok['Faskes'] == st.session_state.faskes_dokter) & (df_antrian_dok['Status_Periksa'] == 'Belum')].tolist()
                        if idx_update:
                            df_antrian_dok.at[idx_update[0], 'Status_Periksa'] = 'Sudah'
                            df_antrian_dok.to_excel(DB_ANTRIAN, index=False)
                        
                        st.success(f"Rekam medis {pilih_pasien} berhasil disimpan.")
                        if status_tindakan == "Rujuk":
                            st.info(f"Pasien dirujuk ke {rs_rujuk}. Diagnosis otomatis terbaca saat pasien mendaftar di faskes tujuan.")
