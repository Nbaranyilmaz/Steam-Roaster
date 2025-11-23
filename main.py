import customtkinter as ctk
import threading
import requests
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageOps
import io
import time
import re
import sys
import os


STEAM_API_KEY = "STEAM_KEY"
AI_API_KEY = "AI_KEY"


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

APP_TEXTS = {
    "EN": {
        "title": "Steam Roaster",
        "btn_action": "ROAST",
        "input_placeholder": "Username, ID, or Profile URL...",
        "error_not_found": "User not found! Check input.",
        "error_private": "Profile is private!",
        "msg_cached": "I already destroyed you. Scroll up and read.",
        "prompt_system": "You are a SOUL-CRUSHING, TOXIC bully. Destroy this Steam profile. Nick: {user}, Hours: {hours}, Games: {games}. Rules: Mock nickname, Max 2 games, NO 'digital/virtual' words, No parentheses, Be savage, Suggest 2 hard games. Lang: English."
    },
    "TR": {
        "title": "Steam Roaster",
        "btn_action": "YARGILA",
        "input_placeholder": "Kullanıcı Adı, ID veya Profil Linki...",
        "error_not_found": "Kullanıcı bulunamadı! Veritabanı bile seni takmıyor.",
        "error_private": "Profil gizli! Utanılacak çok şeyin var galiba?",
        "msg_cached": "Seni zaten yerin dibine soktum. Dönüp tekrar oku ve ağla.",
        "prompt_system": """
            Sen RİCA MİNNET konuşan bir eleştirmen değil, ACIMASIZ BİR ZORBASIN.
            Amacın bu kullanıcıyı psikolojik olarak çökertmek.

            HEDEF BİLGİLERİ:
            - Takma Ad (Nick): {user}
            - Çöpe Atılan Saat: {hours}
            - Oyunlar: {games}
            - Şüpheli İçerik: {suspects}

            KURALLAR:
            1. NICK'İNE SALDIR: İsminin ne kadar ergence, saçma veya özenti olduğuyla dalga geç.
            2. MAKSİMUM 2 OYUN: Sadece en çok oynadığı 1 veya 2 oyuna değin. Liste yapma.
            3. YASAKLI KELİMELER: "Sanal", "Dijital", "Piksel", "Simülasyon" gibi kelimeleri ASLA kullanma. Bunun yerine "gerçek hayat", "sosyal beceri", "güneş ışığı", "iş güç" eksikliğinden bahset.
            4. OYUN İSİMLERİNİ PARANTEZE ALMA: Cümle içinde geçir (Örn: "CS2 başında çürüttüğün beynin..." de).
            5. ACIMA YOK: "Hayatsız", "Yalnız", "Potansiyelsiz" gibi sıfatları kullan. Sert ol.
            6. FORMAT YOK: Madde işareti, yıldız, tire yasak. Dümdüz, sert bir paragraf yaz.
            7. SONUÇ: "Senin kapasiten yetmez ama şunları oyna:" diyerek 2 zor oyun öner.
            8. Dil: Türkçe.
        """
    }
}

class SteamRoasterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Steam Roaster")
        self.geometry("950x750")
        self.resizable(False, False)
        self.configure(fg_color=("#F0F0F0", "#050505"))
        
        # BAŞLANGIÇ DİLİ İNGİLİZCE OLDU
        self.current_lang = "EN" 
        self.last_query = None
        
        # İkon Ayarı
        icon_name = "logo.ico"
        icon_path = icon_name
        if hasattr(sys, "_MEIPASS"):
            icon_path = os.path.join(sys._MEIPASS, icon_name)
        
        try:
            self.iconbitmap(icon_path)
        except:
            pass

        if "BURAYA" in STEAM_API_KEY or not STEAM_API_KEY:
            self.show_error("API Keys are missing in the code!")

        self.init_ui()

    def init_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=40, pady=(30, 20), sticky="ew")
        
        self.lbl_title = ctk.CTkLabel(self.header_frame, text="Steam Roaster", font=("Helvetica", 36, "bold"))
        self.lbl_title.pack(side="left")

        self.controls_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.controls_frame.pack(side="right")

        # Theme Switch
        self.theme_switch = ctk.CTkSwitch(self.controls_frame, text="DARK", command=self.toggle_theme, font=("Arial", 12, "bold"), progress_color="#333")
        self.theme_switch.select()
        self.theme_switch.pack(side="left", padx=15)

        # Lang Switch (Artık EN başlıyor)
        self.lang_switch = ctk.CTkSwitch(self.controls_frame, text="EN", command=self.toggle_language, font=("Arial", 12, "bold"), progress_color="#444", fg_color=("gray", "#222"))
        # self.lang_switch.select() # BU SATIRI SİLDİM, ARTIK SEÇİLİ DEĞİL (EN)
        self.lang_switch.pack(side="left")

        # Input
        self.input_container = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#111111"), corner_radius=15, border_width=1, border_color=("gray", "#222"))
        self.input_container.grid(row=1, column=0, padx=100, pady=10, sticky="ew")
        self.input_container.grid_columnconfigure(0, weight=1)

        self.entry_field = ctk.CTkEntry(self.input_container, height=50, border_width=0, fg_color=("#EBEBEB", "#1a1a1a"), text_color=("black", "white"), placeholder_text=APP_TEXTS["EN"]["input_placeholder"], font=("Arial", 14))
        self.entry_field.grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        # Profile Card
        self.profile_card = ctk.CTkFrame(self, fg_color=("#E0E0E0", "#161616"), corner_radius=15, border_width=1, border_color=("gray", "#333"))
        self.profile_card.grid(row=2, column=0, padx=200, pady=10, sticky="ew")
        self.profile_card.grid_remove()

        self.img_label = ctk.CTkLabel(self.profile_card, text="")
        self.img_label.pack(side="left", padx=20, pady=15)

        self.name_label = ctk.CTkLabel(self.profile_card, text="", font=("Arial", 18, "bold"))
        self.name_label.pack(side="left", pady=5)

        # Button
        self.action_btn = ctk.CTkButton(self, text="ROAST", height=60, corner_radius=30, font=("Arial", 18, "bold"), fg_color=("black", "white"), text_color=("white", "black"), hover_color=("gray", "#e0e0e0"), command=self.on_submit)
        self.action_btn.grid(row=4, column=0, padx=150, pady=20, sticky="ew")

        # Output
        self.output_box = ctk.CTkTextbox(self, corner_radius=15, fg_color=("#FFFFFF", "#080808"), text_color=("black", "#cccccc"), font=("Consolas", 15), border_width=0, wrap="word")
        self.output_box.grid(row=3, column=0, padx=50, pady=10, sticky="nsew")
        self.output_box.insert("0.0", "")
        self.output_box.configure(state="disabled")
        
        self.progress_bar = ctk.CTkProgressBar(self, height=3, progress_color=("black", "white"))
        self.progress_bar.grid(row=5, column=0, sticky="ew")
        self.progress_bar.grid_remove()

    def toggle_theme(self):
        mode = "Dark" if self.theme_switch.get() else "Light"
        ctk.set_appearance_mode(mode)
        self.theme_switch.configure(text=mode.upper())

    def toggle_language(self):
        # Eğer switch açıksa (1) TR, kapalıysa (0) EN
        self.current_lang = "TR" if self.lang_switch.get() else "EN"
        self.lang_switch.configure(text=self.current_lang)
        self.action_btn.configure(text=APP_TEXTS[self.current_lang]["btn_action"])
        self.entry_field.configure(placeholder_text=APP_TEXTS[self.current_lang]["input_placeholder"])

    def process_avatar(self, img_data):
        try:
            img = Image.open(io.BytesIO(img_data)).resize((70,70), Image.Resampling.LANCZOS)
            mask = Image.new("L", (70,70), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 70, 70), fill=255)
            out = ImageOps.fit(img, mask.size, centering=(0.5, 0.5))
            out.putalpha(mask)
            return ctk.CTkImage(light_image=out, dark_image=out, size=(70,70))
        except: return None

    def sanitize_input(self, text):
        text = text.strip()
        if "steamcommunity.com" in text:
            text = text.rstrip('/').split('/')[-1]
        return text

    def clean_response(self, text):
        text = text.replace("*", "").replace("_", "").replace("`", "")
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()

    def show_error(self, message):
        self.finalize_process(message)

    def on_submit(self):
        raw = self.entry_field.get().strip()
        if not raw: return
        
        target = self.sanitize_input(raw)
        
        if target == self.last_query:
            self.animate_text(APP_TEXTS[self.current_lang]["msg_cached"])
            return

        self.action_btn.configure(state="disabled", text="...")
        self.output_box.configure(state="normal"); self.output_box.delete("0.0", "end"); self.output_box.configure(state="disabled")
        self.profile_card.grid_remove(); self.progress_bar.grid(); self.progress_bar.start()
        
        threading.Thread(target=self.run_analysis, args=(target,)).start()

    def run_analysis(self, target):
        try:
            steam_id = target
            if not target.isdigit():
                url = f"http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={STEAM_API_KEY}&vanityurl={target}"
                resp = requests.get(url).json()
                if resp['response']['success'] != 1:
                    raise Exception("UserNotFound")
                steam_id = resp['response']['steamid']
            
            p_url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={STEAM_API_KEY}&steamids={steam_id}"
            p_data = requests.get(p_url).json()['response']['players'][0]
            name = p_data.get('personaname', 'Unknown')
            
            avatar_img = self.process_avatar(requests.get(p_data['avatarfull']).content)
            self.after(0, lambda: self.display_card(name, avatar_img))

            g_url = f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={STEAM_API_KEY}&steamid={steam_id}&include_appinfo=1&format=json"
            g_data = requests.get(g_url).json()
            
            if 'games' not in g_data['response']: raise Exception("PrivateProfile")
            
            games = g_data['response']['games']
            sorted_games = sorted(games, key=lambda x: x['playtime_forever'], reverse=True)[:8]
            games_str = ", ".join([g['name'] for g in sorted_games])
            total_hours = sum([int(g['playtime_forever']/60) for g in games])
            
            suspects = [g['name'] for g in games if any(x in g['name'].lower() for x in ["hentai", "sex", "porn", "furry"])]
            suspect_str = ", ".join(suspects[:3]) if suspects else "None"

            genai.configure(api_key=AI_API_KEY)
            model = genai.GenerativeModel('gemini-flash-latest')
            
            prompt_template = APP_TEXTS[self.current_lang]["prompt_system"]
            final_prompt = prompt_template.format(
                user=name, hours=total_hours, games=games_str, suspects=suspect_str
            )
            
            ai_resp = model.generate_content(final_prompt)
            cleaned_resp = self.clean_response(ai_resp.text)
            
            self.last_query = target
            self.finalize_process(cleaned_resp)

        except Exception as e:
            err_msg = str(e)
            if "UserNotFound" in err_msg: err_msg = APP_TEXTS[self.current_lang]["error_not_found"]
            elif "PrivateProfile" in err_msg: err_msg = APP_TEXTS[self.current_lang]["error_private"]
            elif "429" in err_msg: err_msg = "API Limit Reached. Wait a moment."
            
            self.finalize_process(err_msg)

    def display_card(self, name, img):
        if img: self.img_label.configure(image=img)
        self.name_label.configure(text=name)
        self.profile_card.grid()

    def finalize_process(self, text):
        self.progress_bar.stop(); self.progress_bar.grid_remove()
        self.after(0, lambda: self.action_btn.configure(state="normal", text=APP_TEXTS[self.current_lang]["btn_action"]))
        self.after(0, lambda: self.animate_text(text))

    def animate_text(self, text):
        self.output_box.configure(state="normal"); self.output_box.delete("0.0", "end")
        for char in text:
            self.output_box.insert("end", char); self.output_box.see("end"); self.update(); time.sleep(0.02)
        self.output_box.configure(state="disabled")

if __name__ == "__main__":
    app = SteamRoasterApp()
    app.mainloop()
