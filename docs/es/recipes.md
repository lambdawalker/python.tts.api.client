# Recetas

Ejecuta estos fragmentos dentro de `with TTSClient(...) as client:`. Comprueba las
capacidades y lee las instrucciones antes de solicitar funciones opcionales.

## Referencias y voces

```python
asset = client.upload_asset("reference.wav")
voice = client.register_voice(
    references=[{"asset_id": asset.id, "transcript": "Actual spoken words."}],
    alias="narrator",
)
job = client.generate_speech(text="Hello!", voice={"id": voice.id})
```

Los bytes y transcripciones se conservan. La aplicación proporciona una grabación
y transcripción adecuadas; no hay ASR, remuestreo, limpieza ni sustitución de voces.
`list_voices(model=...)` consulta voces y `delete_voice(voice.id)` elimina una.
El selector exige exactamente un `id` o `alias` no vacío.

## Diseño y conversión

```python
design = client.design_voice(description="Warm, low voice", preview_text="Hello!")
conversion = client.convert_voice(source_asset_id=asset.id, voice={"id": voice.id})
```

Ambas operaciones devuelven trabajos. Usa `wait()` y descarga los recursos de sus
resultados. El diseño no registra automáticamente una voz reutilizable; consulta
las instrucciones del servidor para registrarla después.

## Controles nativos

```python
job = client.generate_speech(
    text="Hello!",
    model="default",
    instructions="Speak calmly",
    output={"format": "wav", "sample_rate": 24000},
)
```

Es ilustrativo: el perfil debe admitir instrucciones, formato y frecuencia. Las
etiquetas nativas van directamente en el texto y los controles documentados en
`extensions`. El cliente valida la estructura, no la semántica nativa. Usa un objeto
de solicitud o campos por palabra clave, nunca ambos. No se eliminan etiquetas.

## Reconexión y progreso

```python
from contextlib import closing

job = client.job("saved-job-id")
with closing(job.events(after="saved-event-id")) as events:
    for event in events:
        print(event.source, event.id, event.event, event.data)
status = job.wait(timeout=60)
```

SSE reanuda con `Last-Event-ID`, suprime repeticiones numéricas monótonas y duplicados
opacos inmediatos, y descarta tramas incompletas. Valores predeterminados:
`reconnect_attempts=3`, `reconnect_delay=1`, `polling_fallback=True`, `poll_interval=1`.
El sondeo produce `source="poll"`, `event="status"`, `id=None`. El servidor debe cerrar
el flujo al terminar. Cierra iteradores abandonados; usa `contextlib.aclosing` en
asyncio. El iterador no tiene plazo total, solo límites de inactividad HTTP.

## Recuperación de envíos

Guarda una clave única por generación prevista. Tras un fallo ambiguo de red, la
aplicación puede reenviar la misma solicitud con la misma clave si el servidor
implementa idempotencia. Otra clave inicia otro trabajo. El SDK no reintenta envíos;
`retryable` solo informa y no activa acciones automáticas.

## Descargas atómicas

```python
client.download_asset(status.results[0].asset_id, "speech.wav")
```

El directorio padre debe existir. El éxito reemplaza el destino atómicamente; un
fallo elimina el temporal y conserva el archivo anterior. Se ignoran URLs recibidas:
la descarga utiliza el servidor configurado y el ID del recurso.
