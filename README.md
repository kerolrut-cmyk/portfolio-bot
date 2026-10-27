# Telegram-бот портфолио Марины Сухаревой

Бот показывает работы, услуги и цены, и принимает заявки. Заявки приходят тебе в Телеграм и пишутся в `applications.db`.

## Что внутри

- `bot.py` — вся логика бота (aiogram 3)
- `content.py` — **твой контент**: имя, услуги, цены, кейсы, контакты. Редактируй только его.
- `media/` — картинки кейсов. Имя файла указывается в `content.py` в поле `images`.
- `applications.db` — база заявок (создаётся сама)
- `make_placeholders.py` — генератор временных обложек, если своих фото пока нет

## Команды бота

`/start` `/portfolio` `/services` `/apply` `/contacts` `/apps` (заявки, только для тебя) `/help`

## Запуск локально

```bash
pip install -r requirements.txt
export BOT_TOKEN=123456:AA...     # от @BotFather
export ADMIN_ID=11111111          # твой Telegram ID, узнай у @userinfobot
python bot.py
```

## Как поменять контент

1. Открой `content.py`.
2. Заполни `NAME`, `ROLE`, `TAGLINE`, `ABOUT`, `CONTACTS`.
3. В `SERVICES` — услуги и цены: `(название, описание, цена)`.
4. В `CASES` — кейсы: заголовок, категория, год, описание, результат, теги, картинки.
5. Перезапусти бота.

Картинки: положи файл в `media/` и пропиши в кейсе `"images": ["media/имя.jpg"]`. Если файла нет, кейс отправится текстом — не сломается.

## Деплой на сервер (VPS)

```bash
sudo apt install python3-venv
scp -r portfolio-bot user@server:/opt/portfolio-bot
ssh user@server
cd /opt/portfolio-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

systemd-юнит `/etc/systemd/system/portfolio-bot.service`:

```ini
[Unit]
Description=Portfolio bot
After=network.target

[Service]
WorkingDirectory=/opt/portfolio-bot
Environment=BOT_TOKEN=123456:AA...
Environment=ADMIN_ID=11111111
ExecStart=/opt/portfolio-bot/.venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now portfolio-bot
sudo journalctl -u portfolio-bot -f
```

## Нет VPS

Любой хостинг для Python-ботов (Railway, Fly.io, Render) подойдёт — там есть переменные окружения `BOT_TOKEN` и `ADMIN_ID`, стартовая команда `python bot.py`.
