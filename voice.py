import streamlit as st
import pandas as pd
import datetime
import torch
import librosa
import speech_recognition as sr
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
import os

# === Memuat model dan processor Whisper dari Hugging Face ===
@st.cache_resource
def load_whisper_model():
    processor = AutoProcessor.from_pretrained("openai/whisper-small")
    model = AutoModelForSpeechSeq2Seq.from_pretrained("openai/whisper-small")
    return processor, model

processor, model = load_whisper_model()

# === Fungsi Pengenalan Suara Menggunakan API Whisper ===
def recognize_speech_from_whisper(audio_file_path):
    try:
        # Membaca file audio dan mengonversi sampling rate ke 16kHz
        audio_input, sample_rate = librosa.load(audio_file_path, sr=16000)
        
        # Menggunakan processor untuk memproses audio input
        inputs = processor(audio_input, sampling_rate=16000, return_tensors="pt")
        
        # Melakukan inferensi dengan model Whisper
        with torch.no_grad():
            # Use the correct key - typically 'input_features' for Whisper
            if "input_features" in inputs:
                generated_ids = model.generate(inputs["input_features"])
            elif "input_values" in inputs:
                generated_ids = model.generate(inputs["input_values"])
            else:
                # Fallback: use the first available tensor
                first_key = list(inputs.keys())[0]
                generated_ids = model.generate(inputs[first_key])
        
        # Mendekodekan hasil inferensi menjadi teks
        transcription = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        return transcription
        
    except Exception as e:
        st.error(f"Error in speech recognition: {str(e)}")
        return "Maaf, tidak dapat mengenali suara. Silakan coba lagi."

# === Fungsi untuk memproses teks pesanan dan menambahkannya ke pesanan ===
def process_order_text(text):
    import re
    
    # Dictionary untuk konversi angka dalam bahasa Indonesia ke digit
    number_words = {
        'satu': 1, 'dua': 2, 'tiga': 3, 'empat': 4, 'lima': 5,
        'enam': 6, 'tujuh': 7, 'delapan': 8, 'sembilan': 9, 'sepuluh': 10,
        'sebelas': 11, 'dua belas': 12, 'tiga belas': 13, 'empat belas': 14, 'lima belas': 15,
        'enam belas': 16, 'tujuh belas': 17, 'delapan belas': 18, 'sembilan belas': 19, 'dua puluh': 20,
        'satu': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
        'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20
    }
    
    def extract_quantity_and_item(text, item_keywords):
        """Ekstrak jumlah dan item dari teks"""
        text = text.lower()
        quantity = 1  # default
        
        # Cari pola angka + item atau item + angka
        for keyword in item_keywords:
            if keyword in text:
                # Cari angka di sekitar keyword
                # Pola: angka + item (contoh: "3 burger", "tiga burger")
                pattern1 = r'(\d+|\w+)\s+' + re.escape(keyword)
                match1 = re.search(pattern1, text)
                
                # Pola: item + angka (contoh: "burger 3", "burger tiga")
                pattern2 = re.escape(keyword) + r'\s+(\d+|\w+)'
                match2 = re.search(pattern2, text)
                
                # Pola: "saya mau 3 burger" atau "pesan 3 burger"
                pattern3 = r'(?:mau|pesan|ingin|order)\s+(\d+|\w+)\s+' + re.escape(keyword)
                match3 = re.search(pattern3, text)
                
                if match1:
                    qty_str = match1.group(1)
                elif match2:
                    qty_str = match2.group(1)
                elif match3:
                    qty_str = match3.group(1)
                else:
                    # Jika tidak ada pola yang cocok, cari angka terdekat
                    numbers_in_text = re.findall(r'\d+', text)
                    if numbers_in_text:
                        qty_str = numbers_in_text[0]  # Ambil angka pertama
                    else:
                        qty_str = None
                
                if qty_str:
                    # Konversi ke angka
                    if qty_str.isdigit():
                        quantity = int(qty_str)
                    elif qty_str in number_words:
                        quantity = number_words[qty_str]
                    else:
                        quantity = 1
                
                return max(1, quantity)  # Minimal 1
        
        return 0  # Item tidak ditemukan
    
    # Dictionary item dengan keywords yang mungkin diucapkan
    items_config = {
        "burger": ["burger", "hamburger"],
        "ayam goreng": ["ayam goreng", "ayam", "fried chicken"],
        "kentang goreng": ["kentang goreng", "kentang", "french fries", "fries"],
        "hot dog": ["hot dog", "hotdog", "sosis"],
        "cola": ["cola", "kola", "pepsi", "soda"],
        "mineral water": ["mineral water", "air mineral", "air", "water"],
        "es krim": ["es krim", "ice cream", "eskrim"]
    }
    
    # Proses setiap item
    items = {}
    for item_name, keywords in items_config.items():
        quantity = extract_quantity_and_item(text, keywords)
        if quantity > 0:
            items[item_name] = quantity
    
    return items

# === OOP Menu Item ===
class MenuItem:
    def __init__(self, name, price):
        self.name = name
        self.price = price

# === OOP Order Logic ===
class Order:
    def __init__(self):
        self.items = []
        self.payment_method = None

    def add_item(self, menu_item, quantity):
        if quantity > 0:
            # Check if item already exists, if yes, update quantity
            for item in self.items:
                if item["Menu"] == menu_item.name:
                    item["Jumlah"] += quantity
                    item["Subtotal"] = item["Harga"] * item["Jumlah"]
                    return
            # If not exists, add new item
            self.items.append({
                "Menu": menu_item.name,
                "Harga": menu_item.price,
                "Jumlah": quantity,
                "Subtotal": menu_item.price * quantity
            })
    
    def remove_item(self, index):
        """Hapus item berdasarkan index"""
        if 0 <= index < len(self.items):
            self.items.pop(index)
    
    def update_item_quantity(self, index, new_quantity):
        """Update jumlah item berdasarkan index"""
        if 0 <= index < len(self.items):
            if new_quantity <= 0:
                self.remove_item(index)
            else:
                self.items[index]["Jumlah"] = new_quantity
                self.items[index]["Subtotal"] = self.items[index]["Harga"] * new_quantity
    
    def clear_empty_items(self):
        """Hapus item dengan jumlah 0"""
        self.items = [item for item in self.items if item["Jumlah"] > 0]

    def get_order_df(self):
        return pd.DataFrame(self.items) if self.items else pd.DataFrame(columns=["Menu", "Harga", "Jumlah", "Subtotal"])

    def get_total(self):
        return sum(item["Subtotal"] for item in self.items)

    def reset(self):
        self.items = []
        self.payment_method = None

    def set_payment_method(self, method):
        self.payment_method = method

    def generate_receipt(self, uang_diterima=None):
        receipt = "=== STRUK PEMBELIAN ===\n"
        for item in self.items:
            receipt += f"{item['Menu']} x{item['Jumlah']} = Rp{item['Subtotal']:,.0f}\n"
        receipt += f"---------------------------\nTotal: Rp{self.get_total():,.0f}\n"
        receipt += f"Metode Bayar: {self.payment_method}\n"

        if uang_diterima is not None:
            if uang_diterima >= self.get_total():
                kembali = uang_diterima - self.get_total()
                receipt += f"Uang Diterima: Rp{uang_diterima:,.0f}\n"
                receipt += f"Uang Kembali: Rp{kembali:,.0f}\n"
            else:
                kekurangan = self.get_total() - uang_diterima
                receipt += f"Uang Diterima: Rp{uang_diterima:,.0f}\n"
                receipt += f"⚠️ Kekurangan: Rp{kekurangan:,.0f}\n"

        receipt += f"Waktu: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        receipt += "===========================\nTerima kasih! 🍽️"
        return receipt

# === Daftar Menu ===
menu_items = [
    MenuItem("🍔 Burger", 25000),
    MenuItem("🍗 Ayam Goreng", 30000),
    MenuItem("🍟 Kentang Goreng", 15000),
    MenuItem("🌭 Hot Dog", 20000),
    MenuItem("🥤 Cola", 10000),
    MenuItem("🥤 Mineral Water", 7000),
    MenuItem("🍦 Es Krim", 12000),
]

# === Streamlit UI ===
st.title("🍔 Mc Ronald Drive-Thru 🍔")

# Initialize session state
if "order" not in st.session_state:
    st.session_state.order = Order()
if "stage" not in st.session_state:
    st.session_state.stage = "ordering"  # ordering, payment, completed
if "last_transcription" not in st.session_state:
    st.session_state.last_transcription = ""


# Menampilkan menu dan harga
st.subheader("Menu Mc Ronald")
menu_df = pd.DataFrame([(item.name, f"Rp{item.price:,.0f}") for item in menu_items], columns=["Menu", "Harga"])
st.dataframe(menu_df, use_container_width=True, hide_index=True)

# Sidebar untuk kategori menu
with st.sidebar:
    st.image("https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExdmF6aGw2YWN6am1zZGo4M2RvOHl2bWZlbXRkbTNjcjAzbzgzOHhkYSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/12OoIZRC435JrcFV6z/giphy.gif", caption="Fast Food Logo", width=300)
    st.title("Menu Ingredient")
    category = st.radio("Pilih kategori:", ["Burger", "Ayam Goreng", "Kentang Goreng", "Hotdog", "Cola", "Mineral Water", "Es Krim"])

    # Tambahkan tombol deskripsi di bawah menu ingredient
    category_descriptions = {
        "Burger": "Burger lezat dengan daging sapi pilihan dan sayuran segar.",
        "Ayam Goreng": "Ayam goreng renyah dengan bumbu khas.",
        "Kentang Goreng": "Kentang goreng gurih dan renyah, cocok untuk camilan.",
        "Hotdog": "Hotdog dengan sosis premium dan saus spesial.",
        "Cola": "Minuman cola dingin yang menyegarkan.",
        "Mineral Water": "Air mineral murni untuk melepas dahaga.",
        "Es Krim": "Es krim manis dan dingin membuat fun."
    }

    if st.button("Tampilkan Deskripsi"):
        st.write(f"**Deskripsi:** {category_descriptions[category]}")

# Tambahkan CSS untuk mempercantik aplikasi
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #fffbe7 0%, #ffe5b4 40%, #f6d365 70%, #fda085 100%);
        background-attachment: fixed;
        min-height: 100vh;
    }
    .stTitle, .stHeader, .stSubheader, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #8B4513 !important;
        text-shadow: 2px 2px 8px #ffd70099, 0 2px 8px #fda08566;
    }
    .stButton>button {
        background: linear-gradient(90deg, #ffd700 0%, #f7971e 100%);
        color: #8B4513;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        box-shadow: 0 2px 8px #fda08533;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #f7971e 0%, #ffd700 100%);
    }
    .stSidebar {
        background: #fffbe7;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Tambahkan header dengan gaya khusus
st.markdown('<h1 style="text-align:center; font-size:2rem; font-family:Comic Sans MS, Comic Sans, cursive; color:#8B4513; font-weight:bold; letter-spacing:2px; margin-bottom:0.5em; text-shadow:2px 2px 8px #ffd70099,0 2px 8px #fda08566;">🍔PAYMENT🍔</h1>', unsafe_allow_html=True)

# === TAHAP PEMESANAN ===
if st.session_state.stage == "ordering":
    st.subheader("🎤 Pemesanan Suara")
    
    # Tampilkan pesanan saat ini jika ada
    if st.session_state.order.items:
        st.subheader("Pesanan Saat Ini:")
        
        # Tampilkan setiap item dengan tombol hapus dan edit
        for idx, item in enumerate(st.session_state.order.items):
            col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])

            with col1:
                st.write(f"**{item['Menu']}** - Rp{item['Harga']:,.0f} x {item['Jumlah']} = Rp{item['Subtotal']:,.0f}")
            
            with col2:
                # Tombol kurangi jumlah
                if st.button("➖", key=f"decrease_{idx}", help="Kurangi 1"):
                    if item['Jumlah'] > 1:
                        item['Jumlah'] -= 1
                        item['Subtotal'] = item['Harga'] * item['Jumlah']
                    else:
                        # Jika jumlah = 1, hapus item
                        st.session_state.order.items.pop(idx)
                    st.rerun()
            
            with col3:
                # Input jumlah langsung tanpa label 'Qty'
                new_qty = st.number_input(
                    label="",  # Menghapus label
                    min_value=0, 
                    value=item['Jumlah'], 
                    key=f"qty_{idx}",
                    label_visibility="collapsed"  # Menyembunyikan label agar lebih sejajar
                )  # Menghapus properti help
                if new_qty != item['Jumlah']:
                    if new_qty == 0:
                        st.session_state.order.items.pop(idx)
                    else:
                        item['Jumlah'] = new_qty
                        item['Subtotal'] = item['Harga'] * item['Jumlah']
                    st.rerun()
            
            with col4:
                # Tombol tambah jumlah
                if st.button("➕", key=f"increase_{idx}", help="Tambah 1"):
                    item['Jumlah'] += 1
                    item['Subtotal'] = item['Harga'] * item['Jumlah']
                    st.rerun()
            
            with col5:
                # Tombol hapus item
                if st.button("🗑️", key=f"delete_{idx}", help="Hapus item"):
                    st.session_state.order.items.pop(idx)
                    st.rerun()

            with col6:
                # Tombol edit item
                pass  # Menghapus tombol edit
        
        st.divider()
        st.write(f"### **Total: Rp{st.session_state.order.get_total():,.0f}**")
    
    # Tombol untuk mulai mendengarkan pesanan suara
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎤 Mulai Bicara", key="voice_button"):
            with st.spinner("🎤 Mendengarkan pesanan..."):
                # Merekam suara menggunakan mikrofon dan menyimpannya ke file WAV sementara
                recognizer = sr.Recognizer()
                microphone = sr.Microphone()

                try:
                    with microphone as source:
                        recognizer.adjust_for_ambient_noise(source, duration=1)
                        audio = recognizer.listen(source, timeout=10, phrase_time_limit=5)

                    with open("temp_audio.wav", "wb") as f:
                        f.write(audio.get_wav_data())

                    # Mengenali suara dengan model Whisper
                    transcription = recognize_speech_from_whisper("temp_audio.wav")
                    st.session_state.last_transcription = transcription

                    # Cleanup temp file
                    if os.path.exists("temp_audio.wav"):
                        os.remove("temp_audio.wav")

                    # Menampilkan hasil transkripsi
                    st.success(f"Pesanan yang dikenali: {transcription}")

                    # Proses transkripsi untuk menambah item ke pesanan
                    items_recognized = process_order_text(transcription)
                    if items_recognized:
                        for item_key, qty in items_recognized.items():
                            # Find matching menu item
                            for menu_item in menu_items:
                                if item_key.replace(" ", "").lower() in menu_item.name.replace(" ", "").lower():
                                    st.session_state.order.add_item(menu_item, qty)
                                    st.success(f"✅ Menambahkan {qty} x {menu_item.name}")
                                    break
                    else:
                        st.warning("Tidak ada item yang dikenali. Silakan coba lagi dengan lebih jelas.")
                        
                except sr.WaitTimeoutError:
                    st.error("Waktu habis. Silakan coba lagi.")
                except Exception as e:
                    st.error(f"Error dalam perekaman: {str(e)}")
    
    with col2:
        if st.button("🛒 Lanjut ke Pembayaran", key="payment_button"):
            if st.session_state.order.items:
                st.session_state.stage = "payment"
                st.rerun()
            else:
                st.warning("Pesanan masih kosong! Silakan pesan terlebih dahulu.")
    
    with col3:
        if st.button("🗑️ Reset Pesanan", key="reset_button"):
            st.session_state.order.reset()
            st.session_state.last_transcription = ""
            st.success("Pesanan direset!")
            st.rerun()

# === TAHAP PEMBAYARAN ===
elif st.session_state.stage == "payment":
    st.subheader("💳 Pembayaran")
    
    # Tampilkan ringkasan pesanan
    st.subheader("Ringkasan Pesanan:")
    order_df = st.session_state.order.get_order_df()
    st.dataframe(order_df, use_container_width=True, hide_index=True)
    
    total = st.session_state.order.get_total()
    st.write(f"### **Total: Rp{total:,.0f}**")
    
    # Input metode pembayaran
    payment_method = st.selectbox("Pilih Metode Pembayaran:", ["Cash", "E-Wallet", "Debit Card"], key="payment_method")
    st.session_state.order.set_payment_method(payment_method)
    
    # Input jumlah uang yang diterima (hanya untuk Cash)
    if payment_method == "Cash":
        uang_diterima = st.number_input(
            "💵 Masukkan uang diterima (Rp):", 
            min_value=0, 
            step=1000, 
            key="uang_diterima"
        )
        
        if uang_diterima > 0:
            if uang_diterima >= total:
                kembalian = uang_diterima - total
                st.success(f"✅ Uang kembali: Rp{kembalian:,.0f}")
                payment_complete = True
            else:
                kekurangan = total - uang_diterima
                st.error(f"⚠️ Uang kurang: Rp{kekurangan:,.0f}")
                payment_complete = False
        else:
            payment_complete = False
    else:
        # Untuk E-Wallet dan Debit Card, tidak perlu input uang
        st.info(f"Silakan lakukan pembayaran melalui {payment_method}")
        uang_diterima = total  # Set equal to total for non-cash payments
        payment_complete = True
    
    # Tombol aksi
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("⬅️ Kembali ke Pemesanan", key="back_to_order"):
            st.session_state.stage = "ordering"
            st.rerun()
    
    with col2:
        if payment_complete and st.button("🖨️ Cetak Struk", key="print_receipt"):
            st.session_state.stage = "completed"
            st.rerun()

# === TAHAP SELESAI ===
elif st.session_state.stage == "completed":
    st.subheader("🎉 Pembayaran Berhasil!")
    
    # Generate dan tampilkan struk
    if st.session_state.order.payment_method == "Cash":
        uang_diterima = st.session_state.get("uang_diterima", st.session_state.order.get_total())
    else:
        uang_diterima = st.session_state.order.get_total()
    
    receipt = st.session_state.order.generate_receipt(uang_diterima)
    st.code(receipt, language="text")
    
    # Tombol untuk pesanan baru
    if st.button("🔄 Pesanan Baru", key="new_order"):
        st.session_state.order.reset()
        st.session_state.stage = "ordering"
        st.session_state.last_transcription = ""
        # Clear the uang_diterima from session state
        if "uang_diterima" in st.session_state:
            del st.session_state["uang_diterima"]
        st.rerun()

# Tampilkan transkripsi terakhir jika ada
if st.session_state.last_transcription and st.session_state.stage == "ordering":
    st.info(f"Transkripsi terakhir: {st.session_state.last_transcription}")