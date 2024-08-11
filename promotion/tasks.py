from classifieds.models import Promotion

from celery import shared_task


@shared_task
def delete_promotion(id):
    try:
        promotion = Promotion.objects.get(id=id)
    except Promotion.DoesNotExist:
        pass
    else:
        promotion.delete()
