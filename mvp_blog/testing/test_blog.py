import pytest
from django.utils import timezone
from datetime import timedelta
from mixer.backend.django import mixer
from blog.models import Post, User, Comment, Tag


@pytest.mark.django_db
def test_get_top_posts_with_most_comments(django_assert_num_queries):
    """
    Напишите метод модели в модели Post для извлечения 5 лучших постов с наибольшим количеством комментариев.
    """

    # array
    for obj in mixer.cycle(15).blend(Post):
        mixer.cycle(1).blend(Comment, post=obj)

    for obj in mixer.cycle(5).blend(Post):
        mixer.cycle(2).blend(Comment, post=obj)

    post = mixer.blend(Post, likes=3)
    mixer.cycle(4).blend(Comment, post=post)

    # act
    with django_assert_num_queries(1):
        top_posts = Post.post_manager.get_top_posts_with_most_comments()

    # assert
    assert len(top_posts) == 5
    assert top_posts[0] == post
    for obj in top_posts[1:]:
        assert obj.total_comments_count() == 2


@pytest.mark.django_db
def test_get_user_posts_last_month(django_assert_num_queries):
    """
    напишите метод queryset в модели Post,
    который принимает User и возвращает все созданные им посты, опубликованные за последние 30 дней.
    """
    # array
    user = mixer.blend(User)

    post = mixer.blend(Post, author=user, published_at=timezone.now() - timedelta(days=15))
    expired_post = mixer.blend(Post, author=user, published_at=timezone.now() - timedelta(days=35))
    recent_post = mixer.blend(Post, author=user, published_at=timezone.now() - timedelta(days=20))

    # act
    with django_assert_num_queries(3):
        user_posts = list(Post.post_manager.get_user_posts_last_month(user))

    # assert
    assert post in user_posts
    assert recent_post in user_posts
    assert expired_post not in user_posts


@pytest.mark.django_db
def test_get_posts_with_tag_and_min_likes(django_assert_num_queries):
    """
        реализуйте метод queryset, который возвращает все посты,
        содержащие определенный тег и имеющие количество лайков больше заданного значения
    """
    # array
    post1 = mixer.blend(Post, likes=10)
    post2 = mixer.blend(Post, likes=5)
    post3 = mixer.blend(Post, likes=10)

    tag_name = 'example_tag'
    any_tag_name = 'any_example_tag'

    tag = mixer.blend(Tag, name=tag_name)
    any_tag = mixer.blend(Tag, name=any_tag_name)

    post1.tags.add(tag)
    post2.tags.add(tag)
    post3.tags.add(any_tag)

    # act
    with django_assert_num_queries(3):
        posts = list(Post.post_manager.get_posts_with_tag_and_min_likes(tag_name, 8))

    # assert
    assert post1 in posts
    assert post2 not in posts
    assert post3 not in posts


@pytest.mark.django_db
def test_total_comments_count():
    """
        Используйте функцию аннотации ORM Django для подсчета количества комментариев к посту и возврата этой информации в запросе.
    """
    # array
    post = mixer.blend(Post)
    mixer.cycle(3).blend(Comment, post=post)

    # act
    total_comments_count = post.total_comments_count()

    # assert
    assert total_comments_count == 3


@pytest.mark.django_db
def test_active_user_manager(django_assert_num_queries):
    user_with_recent_post = mixer.blend(User)
    mixer.cycle(100).blend(Post, author=user_with_recent_post, published_at=timezone.now() - timedelta(days=30))

    user_with_old_post = mixer.blend(User)
    mixer.blend(Post, author=user_with_old_post, published_at=timezone.now() - timedelta(days=70))
    with django_assert_num_queries(1):
        active_users = User.active_user_manager.all()

        assert user_with_recent_post in active_users
        assert user_with_old_post not in active_users


@pytest.mark.django_db
def test_get_top_posts_with_most_comments(django_assert_num_queries):
    """
    Напишите пользовательский метод с использованием raw() для Post для извлечения 5 лучших постов с наибольшим количеством комментариев.
    """

    # array
    for obj in mixer.cycle(15).blend(Post):
        mixer.cycle(1).blend(Comment, post=obj)

    for obj in mixer.cycle(5).blend(Post):
        mixer.cycle(2).blend(Comment, post=obj)

    post = mixer.blend(Post, likes=3)
    mixer.cycle(4).blend(Comment, post=post)

    # act
    with django_assert_num_queries(3):
        top_posts = list(Post.post_manager.get_top_posts_with_most_comments_raw())

    # assert
    assert len(top_posts) == 5
    assert top_posts[0] == post
    for obj in top_posts[1:]:
        assert obj.total_comments_count() == 2


@pytest.mark.django_db
def test_bulk_update_posts_like(django_assert_num_queries):
    # Создаем 3 тестовых поста с разным количеством лайков
    post1 = mixer.blend(Post, likes=10)
    post2 = mixer.blend(Post, likes=5)
    post3 = mixer.blend(Post, likes=20)

    # Собираем список постов для обновления лайков
    posts = [post1, post2, post3]

    # Увеличиваем количество лайков на 5 для каждого поста
    with django_assert_num_queries(1):
        Post.post_manager.bulk_update_posts_like(posts, 5)

    # Проверяем, что количество лайков для каждого поста увеличилось на 5
    post1.refresh_from_db()
    assert post1.likes == 15

    post2.refresh_from_db()
    assert post2.likes == 10

    post3.refresh_from_db()
    assert post3.likes == 25
