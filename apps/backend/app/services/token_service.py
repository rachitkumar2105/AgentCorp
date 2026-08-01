from app.core.jwt import create_access_token


class TokenService:
    @staticmethod
    def generate(user_id: int) -> str:
        return create_access_token(str(user_id))