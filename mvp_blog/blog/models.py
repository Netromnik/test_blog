from datetime import timedelta

from django.db import models
from django.utils import timezone


class ActiveUserManager(models.Manager):
    def get_queryset(self):
        last_60_days = timezone.now() - timezone.timedelta(days=60)
        return super().get_queryset().filter(post__published_at__gte=last_60_days).distinct()


class User(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    active_user_manager = ActiveUserManager()


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)


class PostManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('author').prefetch_related('tags', 'comment_set')

    def get_top_posts_with_most_comments(self):
        """Извлечение лучших постов с наибольшим количеством комментариев"""
        return self.get_queryset().annotate(num_comments=models.Count('comment')).order_by('-num_comments')[:5]

    def get_user_posts_last_month(self, author: User ):
        """Извлечение всех постов определенного пользователя, опубликованных за последний месяц"""
        return self.get_queryset().filter(author=author, published_at__gte=timezone.now() - timedelta(days=30))

    def get_posts_with_tag_and_min_likes(self, tag_name, min_likes):
        """Извлечение постов с определенным тегом и количеством лайков больше определенного значения"""
        return self.get_queryset().filter(tags__name=tag_name, likes__gt=min_likes)

    def get_top_posts_with_most_comments_raw(self):
        post_table = self.model._meta.db_table
        comment_table = self.model._meta.get_field('comment').related_model._meta.db_table

        raw_query = f'''
            SELECT p.id, p.title, COUNT(c.id) AS comment_count
            FROM {post_table} p
            LEFT JOIN {comment_table} c ON p.id = c.post_id
            GROUP BY p.id
            ORDER BY comment_count DESC
            LIMIT 5
        '''
        return list(self.raw(raw_query))

    def bulk_update_posts_like(self, posts: list['Post'], like: int):
        """ Массовое обновление лайков """
        self.bulk_update((setattr(post, 'likes', post.likes + like) or post for post in posts), ['likes'])


class Post(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    published_at = models.DateTimeField()
    tags = models.ManyToManyField(Tag)
    likes = models.PositiveIntegerField(default=0)
    post_manager = PostManager()

    def total_comments_count(self):
        """Подсчет общего количества комментариев к посту"""
        return self.comment_set.count()


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
