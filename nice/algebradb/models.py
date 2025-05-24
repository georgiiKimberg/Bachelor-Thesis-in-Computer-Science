from django.db import models


class Sekvens(models.Model):
    sekvens = models.TextField()
    n_param = models.IntegerField()
    a_param = models.TextField()
    family = models.IntegerField(null=True, blank=True)


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['sekvens', 'n_param', 'a_param'], name='unique_sekvens_params'
            )
        ]


