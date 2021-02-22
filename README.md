# utn-frsn-news

Buscar las últimas noticias de la UTN FRSN y publicarlas en un canal de Telegram

# TODO

- Guardar datos en MongoDB
- Comparar y revisar que no existan las URLs en MongoDB
    - Recién ahí obtener y leer las noticias para subirlas a MongoDB
- Una vez listas las nuevas noticias, publicarlas en el canal de Telegram
- Dormir 1 hora y volver a buscar nuevas noticias
    - Guardar la última ejecución en MongoDB y calcular de ahí si tiene que seguir durmiendo o no
    - Con esto se permite que aunque la instancia de este servicio muera y luego sea revivida, se sepa igual si se tiene que volver a buscar noticias o no
- Agregar al inicio de la Raspberry Pi la ejecución de este programa
- Modularizar código
