import fal_client
from cloud import upload_image_to_cloudinary  # Импортируем функцию загрузки в Cloudinary


def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
            print(log["message"])


async def process_images(state):
    data = await state.get_data()
    clothes_image_path = data.get('clothes')
    person_image_path = data.get('photo')

    # Загружаем изображения в Cloudinary
    human_image_url = await upload_image_to_cloudinary(person_image_path)
    garment_image_url = await upload_image_to_cloudinary(clothes_image_path)

    # Вызов нейросети с полученными URL
    response = fal_client.subscribe(
        "fal-ai/idm-vton",
        arguments={
            "human_image_url": human_image_url,
            "garment_image_url": garment_image_url,
            "description": ""
        },
        with_logs=True,
        on_queue_update=on_queue_update,
    )

    # Убедимся, что возвращаем только один объект
    if response and isinstance(response, dict):
        return response.get('image', {}).get('url')
    return None
