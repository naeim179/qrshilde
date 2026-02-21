import flet as ft
import requests

SERVER_URL = "http://127.0.0.1:8000"

def main(page: ft.Page):
    page.title = "QrShilde Mobile"
    page.theme_mode = "light"
    page.scroll = "auto"
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"
    
    img_picked = ft.Image(src="", width=250, height=250, visible=False, border_radius=10)
    status_text = ft.Text("Ready for Secure Scan", size=16, color="blue")
    progress_ring = ft.ProgressRing(visible=False)
    result_card = ft.Container(visible=False)

    def on_file_result(e):
        if e.files:
            path = e.files[0].path
            img_picked.src = path
            img_picked.visible = True
            page.update()
            analyze_image(path)

    picker = ft.FilePicker(on_result=on_file_result)
    page.overlay.append(picker)

    def analyze_image(path):
        status_text.value = "Analyzing... Please wait"
        progress_ring.visible = True
        result_card.visible = False
        page.update()
        
        try:
            with open(path, "rb") as f:
                res = requests.post(f"{SERVER_URL}/api/analyze", files={"file": f})
            
            if res.status_code == 200:
                show_results(res.json())
            else:
                status_text.value = f"Error: {res.status_code}"
        except Exception as ex:
            status_text.value = "Connection Failed"
            print(ex)
        
        progress_ring.visible = False
        page.update()

    def show_results(data):
        score = data.get("risk_score", 0)
        color = "green" if score < 30 else "orange" if score < 70 else "red"
        
        result_card.content = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon("security", color=color),
                    ft.Text(data.get("risk_level", "UNKNOWN"), size=25, color=color, weight="bold"),
                ], alignment="center"),
                ft.ProgressBar(value=score/100, color=color),
                ft.Text(f"Risk Score: {score}/100"),
                ft.Divider(),
                ft.Markdown(data.get("report", "No Report Data")),
            ]),
            padding=20, border_radius=10, bgcolor="#f5f5f5"
        )
        result_card.visible = True
        status_text.value = "Scan Complete"
        page.update()

    page.add(
        ft.Column([
            ft.Icon("qr_code_scanner", size=60, color="blue900"),
            ft.Text("QrShilde", size=30, weight="bold"),
            img_picked,
            ft.ElevatedButton("Select QR Image", on_click=lambda _: picker.pick_files()),
            progress_ring,
            status_text,
            result_card
        ], horizontal_alignment="center")
    )

ft.app(target=main)
