# UTN FRSN News

## Introducción

Scripts para la obtención y publicación de las últimas noticias de la facultad en una canal de Telegram.

> Canal de Telegram: https://t.me/utnfrsnnews

Consta de dos scripts principales:

- Scraper (obtención de datos)
- Messenger (envío de mensajes por Telegram)

## Scraper

Corre a cada hora y obtiene el histórico de las noticias (no hay otra forma). Compara las URLs de estas noticias con las existentes en la base de datos. Si hay alguna URL que no está en la DB, entonces procede a scrapear la noticia e insertar una tarea en la cola de mensajeo para que más tarde se envie por Telegram.

## Messenger

Utiliza un sistema de cola de trabajo para mandar los mensajes con las noticias. Corre a cada hora (inicia unos minutos después que el scraper, para que tome las nuevas noticias que este genere). Obtiene las tareas sin procesar, y toma de ellas la URL de la noticia. Con esa URL busca los datos en la DB para mandar el mensaje de la noticia y su respectiva imagen. Por último manda el mensaje contruido a partir de esa información.

## Base de Datos

Se utiliza MongoDB (base de datos open source) y como host se utiliza a su propia compañía que da host gratuito bajo unos límites que son sumamente suficientes para la aplicación de este proyecto.

En cuanto a la estructura:

- se utiliza una única base de datos llamada `news_db`
- dentro de esa DB, hay 2 colecciones:
  - `messagerQueue` (**TODO**: arreglar este nombre)
  - `news`

`messagerQueue` tiene la cola de trabajo (aunque se podría usar Redis para ser más eficiente, pero para nuestra aplicación es más que suficiente, de todas formas no se descarta que en el futuro se pueda aplicar Redis para aprender cómo usarlo). La estructura de los datos es:

- `_id` ObjectId de MongoDB
- `url` de la noticia
- `insertedDate` fecha de inserción
- `lastUpdateDate` última actualización
- `status` estado de procesamiento
  - `0`: sin procesar
  - `1`: procesado exitosamente
  - `-1`: error

`news` contiene todo el texto de la noticia, la url de la foto y además mediciones de tiempo para el parseado y la espera de la respuesta del sitio web. La estructura de los datos es la siguiente:

- `_id` ObjectId de MongoDB
- `insertedDatetime` fecha de inserción
- `url` de la noticia
- `title` título de la noticia
- `body` cuerpo de la noticia
- `urlPhoto` url para la foto de la noticia
- `responseElapsedTime` tiempo de respuesta de la petición http al servidor web de la facultad
- `parseElapsedTime` tiempo empleado en el parseado de la información en el html de la página

## Infraestructura

- Base de datos: MongoDB
  - Host: https://www.mongodb.com/
- Cron y corrida de scripts en Heroku usando un add-on llamado Heroku Scheduler
  - Heroku Scheduler: https://elements.heroku.com/addons/scheduler
  - Blog donde explica cómo usarlo: https://paulkarayan.tumblr.com/post/72895819532/how-to-run-a-daily-script-on-heroku
