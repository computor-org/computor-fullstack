from ctutor_backend.client.crud_client import CustomClient

if __name__ == '__main__':
    resp1 = CustomClient("http://localhost:8000",("admin","admin")).list("/students/course-contents")
    resp2 = CustomClient("http://localhost:8000",("admin","admin")).list("/students/submission-groups")

    import json
    print(json.dumps(resp1,indent=2))
    print("####################################")
    print(json.dumps(resp2,indent=2))