import configparser
import shutil
import os
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import threading
import time
import atexit
import psutil
LOCK_FILE = 'program.lock'


def check_previous_instance():
    if os.path.exists(LOCK_FILE):
        with open(LOCK_FILE, 'r') as file:
            pid = int(file.read().strip())
        try:
            process = psutil.Process(pid)
            process.terminate()
            log(f"Terminated previous instance with PID {pid}")
        except psutil.NoSuchProcess:
            log(f"No running process found with PID {pid}")
        except Exception as e:
            log(f"Failed to terminate process with PID {pid}: {e}")
        os.remove(LOCK_FILE)


# 默认配置
default_config = {
    'General': {
        'repeat_time_minutes': '181'
    },
    'BrowserOptions': {
        'show_chrome': 'False',
        'mute_audio': 'True',
        'autoplay': 'True'
    },
    'Proxy': {
        'server_address': '127.0.0.1',
        'server_port': '12345'
    },
    'Video1': {
        'url': 'https://www.youtube.com/watch?v=C23mg-06250&list=UULFJmURep1NAeRc1XHvSh3b3A',
        'play_time_minutes': '180',
        'loop_count': '1'
    },
    'Video2': {
        'url': 'https://www.youtube.com/watch?v=nIQs91xBFss&list=UULFJmURep1NAeRc1XHvSh3b3A&index=8',
        'play_time_minutes': '60',
        'loop_count': '3'
    },
    'Video3': {
        'url': 'https://www.youtube.com/watch?v=kL88jnEd7d4&list=UULFJmURep1NAeRc1XHvSh3b3A&index=15',
        'play_time_minutes': '30',
        'loop_count': '6'
    },
    # ... 其他视频配置
}

video_status = {}


def backup_config_file():
    log("Config file backed up.")
    if os.path.exists('config.ini'):
        backup_filename = f'backup_config.ini'
        shutil.copy('config.ini', backup_filename)


def load_config():
    backup_config_file()
    config = configparser.ConfigParser()
    if not os.path.exists('config.ini'):
        config.read_dict(default_config)
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
    else:
        config.read('config.ini')
        for section, options in default_config.items():
            for option, value in options.items():
                if not config.has_option(section, option):
                    config.set(section, option, value)
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
    log("Config loaded.")
    return config


def open_youtube_video(config):
    try:
        chrome_options = webdriver.ChromeOptions()
        if not config.getboolean('BrowserOptions', 'show_chrome'):
            chrome_options.add_argument("--headless")
            log("--Config headless.")
        if config.getboolean('BrowserOptions', 'mute_audio'):
            chrome_options.add_argument("--mute-audio")
            log("--Config mute-audio.")
        if config.getboolean('BrowserOptions', 'autoplay'):
            chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
            log("--Config autoplay.")
        # 从配置文件中读取代理服务器设置
        proxy_server_address = config.get('Proxy', 'server_address', fallback='127.0.0.1')
        proxy_server_port = config.get('Proxy', 'server_port', fallback='12345')
        log("--Config proxy_server_address ["+proxy_server_address+"].")
        log("--Config proxy_server_port ["+proxy_server_port+"].")
        chrome_options.add_argument(f"--proxy-server=socks5://{proxy_server_address}:{proxy_server_port}")
        log("--Config proxy socks5://"+proxy_server_address+":"+proxy_server_port)
        ChromeDriverManager().install()
        driver = webdriver.Chrome(options=chrome_options)
        atexit.register(driver.quit)  # 确保在程序退出时关闭浏览器
        return driver
    except WebDriverException as e:
        print(f"Failed to start Chrome: {e}")
        log(f"Failed to start Chrome: {e}")
        return None


def play_video(driver, url, play_time_minutes, loop_count):
    video_status[url] = {"loops_remaining": loop_count, "current_loop": 0}
    for i in range(loop_count):
        video_status[url]["current_loop"] = i + 1
        try:
            driver.execute_script(f"window.open('{url}');")
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(play_time_minutes * 60)
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        except WebDriverException as e:
            # print(f"An error occurred while playing video: {e}")
            log(f"An error occurred while playing video: {e}")
    del video_status[url]


def print_status():
    current_tab_index = 0
    while True:
        status_message = f"\n        Status update at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        for url, status in video_status.items():
            status_message += f"\n        URL: {url}\n        Current Loop: {status['current_loop']}/{status['loops_remaining']}"
        
        # 切换到下一个标签页
        if driver.window_handles:
            current_tab_index = (current_tab_index + 1) % len(driver.window_handles)
            driver.switch_to.window(driver.window_handles[current_tab_index])
            status_message += f"\n        Switched to tab {current_tab_index + 1}/{len(driver.window_handles)}"
        else:
            status_message += "\n        No tabs to switch to."
        
        status_message += f"\n        Current Tabs: {[tab for tab in driver.window_handles]}"
        log(status_message)
        time.sleep(60)

def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(message)
    with open('log.txt', 'a') as log_file:
        log_file.write(f'{timestamp} - {message}\n')

def main():
    check_previous_instance()  # 检查并终止先前的程序实例
    with open(LOCK_FILE, 'w') as file:
        file.write(str(os.getpid()))  # 创建锁文件并写入当前进程的 PID
        log('Program id:['+str(os.getpid())+"] .")
    global driver
    with open('log.txt', 'w') as log_file:  # 覆写log.txt
        log_file.write('')
    log("WangZHen Loading!")
    log('Program started.')
    config = load_config()
    if not config:
        log("Failed to load config. Exiting.")
        return

    while True:
        with open(LOCK_FILE, 'w') as file:
            file.write(str(os.getpid()))  # 创建锁文件并写入当前进程的 PID
            log('Program id:['+str(os.getpid())+"] .")

        driver = open_youtube_video(config)
        if driver:
            threads = []
            status_thread = threading.Thread(target=print_status)
            status_thread.start()
            try:
                for section in config.sections():
                    if section.startswith('Video'):
                        url = config.get(section, 'url')
                        play_time_minutes = config.getint(section, 'play_time_minutes')
                        loop_count = config.getint(section, 'loop_count')
                        thread = threading.Thread(target=play_video, args=(driver, url, play_time_minutes, loop_count))
                        threads.append(thread)
                        thread.start()

                for thread in threads:
                    thread.join()
            except Exception as e:
                log(f"An error occurred: {e}")
            finally:
                driver.quit()
                status_thread.join()
                os.remove(LOCK_FILE)  # 在程序结束时删除锁文件
                log('Remove Lock')

        else:
            log(f"Failed to start Chrome. Retrying in {config.get('General', 'repeat_time_minutes')} minutes.")
            time.sleep(config.getint('General', 'repeat_time_minutes') * 60)
            os.remove(LOCK_FILE)  # 在程序结束时删除锁文件
            log('Remove Lock')

if __name__ == "__main__":
    main()