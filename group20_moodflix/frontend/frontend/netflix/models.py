from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
CHARS_MAX_LENGTH: int = 150

class Category(models.Model):
    """Category model class."""
    class GenreChoices(models.TextChoices):
        ACTION = "Action", "Action"
        ADVENTURE = "Adventure", "Adventure"
        COMEDY = "Comedy", "Comedy"
        DRAMA = "Drama", "Drama"
        FANTASY = "Fantasy", "Fantasy"
        HORROR = "Horror", "Horror"
        MYSTERY = "Mystery", "Mystery"
        ROMANCE = "Romance", "Romance"
        SCIFI = "Sci-Fi", "Sci-Fi"
        THRILLER = "Thriller", "Thriller"
        DOCUMENTARY = "Documentary", "Documentary"
        ANIMATION = "Animation", "Animation"
        MUSICAL = "Musical", "Musical"
        CRIME = "Crime", "Crime"
        FAMILY = "Family", "Family"
        HISTORICAL = "Historical", "Historical"
        WESTERN = "Western", "Western"
        BIOGRAPHY = "Biography", "Biography"
        WAR = "War", "War"
        INDIE = "Indie", "Indie"

    name = models.CharField(
        max_length=20,
        choices=GenreChoices.choices,
    )
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Tag model class."""

    name = models.CharField(max_length=CHARS_MAX_LENGTH, blank=True)
    description = models.TextField(blank=True, null=True)


    def __str__(self):
        return self.name


class Movie(models.Model):
    """Movie model class."""
    class LanguageChoices(models.TextChoices):
        EN = 'english', 'english'
        HI = 'hindi', 'hindi'
    class TypeChoices(models.TextChoices):
        S = "short","short"
        A = "average","average"
        L = "long","long"
        SS = "shortseries","shortseries"
        LS = "longseries","longseries"
    name = models.CharField(max_length=CHARS_MAX_LENGTH, blank=True)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE,null=True)
    # category = models.ManyToManyField(Category)
    tags = models.ManyToManyField(Tag)
    watch_count = models.IntegerField(default=0)
    file = models.FileField(upload_to='movies/')
    preview_image = models.ImageField(upload_to='preview_images/',default="preview_images/r2.PNG")
    year=models.IntegerField(default=2000,null=True)
    director=models.CharField(max_length=300,null=True)
    cast=models.JSONField(default=list,null=True)
    language=models.CharField(
        max_length=20,
        default="English",null=True
    )
    # type=models.CharField(
    #     max_length=20,
    #     choices=TypeChoices,
    #     null=True
    # )
    length=models.IntegerField(null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class User(models.Model):

    class MoodChoices(models.TextChoices):
        HAPPY = "happy", "Happy"
        SAD = "sad", "Sad"
        ANGRY = "angry", "Angry"
        NOSTALGIC = "nostalgic", "Nostalgic"
        ANXIOUS = "anxious", "Anxious"
        EXCITED = "excited", "Excited"
        ROMANTIC = "romantic", "Romantic"
        HEARTBROKEN = "heartbroken", "Heartbroken"

    username = models.CharField(max_length=255, unique=True, null=True, blank=True)
    fullname = models.CharField(max_length=1000,null=True)
    age=models.IntegerField()
    previous_watch=models.ManyToManyField(Movie,related_name='previous_for_user')
    mood=models.CharField(
        max_length=20,
        choices=MoodChoices.choices,
        null=True
    )
    preferred_genre=models.ManyToManyField(Category)
    sub_genre=models.JSONField(default=list,null=True)
    year=models.IntegerField(null=True)
    director=models.CharField(max_length=300,null=True)
    cast=models.JSONField(default=list,null=True)
    language=models.CharField(
        max_length=20,
    )
    era = models.CharField(max_length=300,null=True)
    actors=models.JSONField(default=dict,null=True)
    similar_movies=models.ManyToManyField(Movie,related_name='similar_for_users')
    date_created = models.DateTimeField(auto_now_add=True)
    recommended_ids=models.JSONField(default=list)
