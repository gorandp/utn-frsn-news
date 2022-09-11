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
- Hosting: Google Cloud Platform (GCP)
  - Servicios usados: Cloud Functions, Cloud Scheduler, Cloud Build, Pub/Sub
  - Quota gratuita: https://cloud.google.com/free/docs/free-cloud-features?hl=es#free-tier-usage-limits

Anteriormente esta aplicación se hosteaba en Heroku pero a partir del 28/11/2022 sus planes gratuitos serán removidos (https://help.heroku.com/RSBRUH58/removal-of-heroku-free-product-plans-faq).

## Variables de entorno

Es importante destacar que el código fuente no contiene las llaves de acceso a la base de datos ni tampoco a la api de Telegram. Es por ello que se debe configurar mediante variables de entorno.

Dependiendo del entorno, se puede configurar de varias formas. Durante el desarrollo o testeo local de este programa se puede utilizar un archivo `.env` al cual se le pone el siguiente contenido:

```
TELEGRAM_API_KEY="..."
DB_CONNECTION_STRING="..."
LOGGER_LEVEL=INFO
TIMEOUT=180
```

Notar que hay 4 variables de entorno.

- `TELEGRAM_API_KEY` llave de acceso al bot de Telegram
- `DB_CONNECTION_STRING` string que contiene usuario y contraseña, la cual da el acceso completo a la DB
- `LOGGER_LEVEL` menor nivel de logs a mostrar
  - En el ejemplo pongo `INFO` pero pueden ser: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` (o `FATAL`)
- `TIMEOUT` tiempo de espera de la petición de HTTP (luego de esto, se corta la petición y sigue la ejecución del programa, que puede volver a realizar la petición o marcarla como error)

Para el deploy en GCP, se hace uso de un archivo YAML. Básicamente consiste en copiar el archivo `.env` con el nombre `.env.yaml` y luego cambiar los signos `=` por `: ` (notar el espacio luego del ":"). Por último se le pone comillas al valor de TIMEOUT, es decir que quedaría así `TIMEOUT: "180"`.

## Google Cloud Platform

A fines de acortar este README, no se explica cómo crearse una cuenta en GCP, cómo instalar Google Cloud CLI, ni tampoco se profundiza mucho en los servicios utilizados de GCP. Al final de esta sección hay a disposición unos links con info útil sobre estos temas.

El esquema de cómo funciona la infra es el siguiente:
- 2 temas Pub/Sub. Uno para el scraper y otro para el messenger
- 2 functions que se subscriben al tema correspondiente Pub/Sub
- 2 scheduled jobs que publican un mensaje en el tema Pub/Sub cada 1 hora para activar la function deseada

El deploy de las functions y la creación de los scheduled jobs se hace desde la CLI de gcloud.

### Deploy functions

```bash
# Template
gcloud functions deploy [FUNCTION_NAME] --entry-point main --runtime python37 --trigger-resource [TOPIC_NAME] --trigger-event google.pubsub.topic.publish --timeout 540s
```

```bash
# Scraper
gcloud functions deploy scraper_func --entry-point main_scraper --runtime python37 --trigger-resource scraper-pubsub-topic --trigger-event google.pubsub.topic.publish --timeout 540s --env-vars-file .env.yaml
# Messenger
gcloud functions deploy messenger_func --entry-point main_messenger --runtime python37 --trigger-resource messenger-pubsub-topic --trigger-event google.pubsub.topic.publish --timeout 540s --env-vars-file .env.yaml
```

### Schedule jobs

```bash
# Template
# gcloud scheduler jobs create pubsub [JOB_NAME] --schedule [SCHEDULE] --topic [TOPIC_NAME] --message-body [MESSAGE_BODY]
```

```bash
# Scraper
gcloud scheduler jobs create pubsub scraper_job --schedule "30 * * * *" --topic scraper-pubsub-topic --message-body "Scraper job once per hour at minute 30."
# Messenger
gcloud scheduler jobs create pubsub messenger_job --schedule "40 * * * *" --topic messenger-pubsub-topic --message-body "Messenger job once per hour at minute 40."
```

### Referencias externas útiles

- GCP: https://cloud.google.com/
- Instalar Google Cloud CLI: https://cloud.google.com/sdk/docs/install-sdk
- Schedule a recurring python script: https://cloud.google.com/blog/products/application-development/how-to-schedule-a-recurring-python-script-on-gcp
- El uso de un archivo externo para las variables de entorno: https://cloud.google.com/functions/docs/configuring/env-var
