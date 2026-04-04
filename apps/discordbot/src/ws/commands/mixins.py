class DiscordUserMixin:

    def get_errors(self):
        if not self.user_id:
            return self.response_error("missing 'discord_id'")
        return super().get_errors()

    def get_objects(self):
        self.user_id = self.data.get("discord_id")
        super().get_objects()
