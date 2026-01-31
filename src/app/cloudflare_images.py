from pyodide.ffi import to_js
from pyodide.http import pyfetch
from .logger import LogWrapper


class CloudflareConfig:
    ACCOUNT_ID: str = ""
    IMAGES_ACCOUNT_HASH: str = ""
    IMAGES_API_TOKEN: str = ""

    @classmethod
    def setup(
        cls,
        account_id: str,
        images_account_hash: str,
        images_api_token: str,
    ):
        """Cloudflare credentials & identifiers configuration setup

        :param account_id: Cloudflare Account ID
        :type account_id: str
        :param images_account_hash: Cloudflare Account hash
        :type images_account_hash: str
        :param images_api_token: Images API token
        :type images_api_token: str
        """
        cls.ACCOUNT_ID = account_id
        cls.IMAGES_ACCOUNT_HASH = images_account_hash
        cls.IMAGES_API_TOKEN = images_api_token


class CloudflareImages(LogWrapper):
    async def upload(
        self,
        image_filename: str,
        image_data: bytes,
    ) -> str | None:
        """Upload an image to Cloudflare Images.

        Returns the image identifier.

        :param image_filename: Filename
        :type image_filename: str
        :param image_data: Image content
        :type image_data: bytes
        :return: Image ID
        :rtype: str | None
        """
        from js import Blob, FormData

        blob = Blob.new(to_js([image_data]))
        form_data = FormData.new()
        form_data.append("file", blob, image_filename)
        form_data.append("requireSignedURLs", "false")  # We want public URLs
        response = await pyfetch(
            f"https://api.cloudflare.com/client/v4/accounts/{CloudflareConfig.ACCOUNT_ID}/images/v1",
            method="POST",
            headers={
                "Authorization": f"Bearer {CloudflareConfig.IMAGES_API_TOKEN}",
            },
            body=form_data,
        )
        if response.status != 200:
            self.logger.error(
                f"Cloudflare Images upload failed with status {response.status}",
            )
            content = await response.text()
            self.logger.error(f"Response content: {content}")
            return None
        data = await response.json()
        if not data.get("success"):
            self.logger.error(
                f"Cloudflare Images upload failed: {data.get('errors')}",
            )
            return None
        # self.logger.info(f"result {data['result']}")
        # self.logger.info(f"result variants {data['result']['variants']}")
        return data["result"]["id"]

    @staticmethod
    def get_public_url(image_id: str) -> str:
        return (
            f"https://imagedelivery.net/{CloudflareConfig.IMAGES_ACCOUNT_HASH}"
            f"/{image_id}/public"
        )
