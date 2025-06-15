import requests
import os
from tqdm import tqdm
from parsel.selector import Selector
from yt_dlp import YoutubeDL
from pathlib import Path

domain = "https://plataforma.pythonando.com.br"



def get_session_id():
    session = requests.Session()
    user_pass = input("email:senha ")

    login_page_html = requests.get(f"{domain}/usuarios/login/").text
    login_tree = Selector(text=login_page_html)
    csrf_token = login_tree.css("input[name='csrfmiddlewaretoken']::attr(value)").get()

    form_data = {
        'csrfmiddlewaretoken': csrf_token,
        'username': user_pass.split(":")[0],
        'password': user_pass.split(":")[1],
    }


    
    response = session.post(
        f"{domain}/usuarios/login/?next=/membros/",
        data=form_data,
        cookies={'csrftoken': csrf_token},
        allow_redirects=True,
        headers={
            'Host': 'plataforma.pythonando.com.br',
        },
    )
    
    if response.status_code != 200:
        print(f"Erro ao fazer login: {response.status_code}")
        raise Exception("Login failed")
    

    session_id = session.cookies.get("sessionid")
    print(f"Session ID: {session_id}")
    if not session_id:
        print("Falha ao obter session ID. Verifique suas credenciais.")
        raise Exception("Session ID not found")
        
    return session_id




def download():
    cookies = {
        'sessionid': get_session_id(),
    }

    response = requests.get(f"{domain}/membros/curso/python-full", cookies=cookies)
    html = response.text
    html_tree = Selector(text=html)

    modules = html_tree.css("#accordionExample div.card")
    module_index = 0
    for module in tqdm(modules):
        module_title = f'{module_index:03d} {module.css(".titulo_modulo::text").get().strip()}'

        lectures = module.css("a[href*='/membros/curso/python-full?atual_aula_curso=']::attr(href)").getall()
        for lecture in lectures:
            lecture_response = requests.get(f"{domain}{lecture}", cookies=cookies)
            lecture_html = lecture_response.text
            lecture_html_tree = Selector(text=lecture_html)

            lecture_title = lecture_html_tree.css(".col-md h3::text").get().strip()
            panda_lecture_m3u8_id = lecture_html_tree.css("a[href*='https://player-vz-05415a72-468.tv.pandavideo.com.br']::attr(href)").get().split("v=")[-1]

            # kkkkkkkkkkkkkkkk panda sempre seguro
            panda_lecture_m3u8_url = f"https://b-vz-05415a72-468.tv.pandavideo.com.br/{panda_lecture_m3u8_id}/playlist.m3u8.beta"

            path = Path(f"pythonando/{module_title}/{lecture_title}")
            os.makedirs(path, exist_ok=True)
            ydl_opts = {
                'external_downloader': 'aria2c',
                'format': 'worst',
                'quiet': True,
                'no_warnings': True,
                'logger': None,
                'progress_hooks': [],
                'outtmpl': f'{path}/video.%(ext)s',
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([panda_lecture_m3u8_url])

        module_index += 1



if __name__ == "__main__":
    download()