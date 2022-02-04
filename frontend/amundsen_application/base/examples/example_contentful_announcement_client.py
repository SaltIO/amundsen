import contentful
from rich_text_renderer import RichTextRenderer

from flask import current_app as app

from amundsen_application.models.announcements import Announcements, Post
from amundsen_application.base.base_announcement_client import BaseAnnouncementClient

# 1.) Add contentful and rich_text_renderer to requirements.txt file
# 2.) Configure contentful space with matching announcement content model
# 3.) Set the three application configuration variables
class ContentfulAnnouncementClient(BaseAnnouncementClient):
    def __init__(self) -> None:
        self.content_type = app.config["ANNOUNCEMENT_CLIENT_CONTENTFUL_CONTENT_TYPE"]
        self.client = contentful.Client(
          app.config["ANNOUNCEMENT_CLIENT_CONTENTFUL_SPACE"],
          app.config["ANNOUNCEMENT_CLIENT_CONTENTFUL_TOKEN"]
        )
        self.renderer = RichTextRenderer()

    def get_posts(self) -> Announcements:
        entries = self.client.entries({'content_type': self.content_type})

        """
        Returns an instance of amundsen_application.models.announcements.Announcements, which should match
        amundsen_application.models.announcements.AnnouncementsSchema
        """
        posts = []

        for row in entries:
            post = Post(title=row.title,
                        date=row.date.strftime('%b %d %Y %H:%M:%S'),
                        html_content=self.renderer.render(row.content))
            posts.append(post)

        return Announcements(posts)