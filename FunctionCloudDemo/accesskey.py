# add a quota project to your application-default credentials
# gcloud auth application-default set-quota-project <YOUR PROJECT ID>
from google.cloud import secretmanager
def access_secret_version(project_id, secret_id, version_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")
host = access_secret_version('xxxx','host','1')
print(host)