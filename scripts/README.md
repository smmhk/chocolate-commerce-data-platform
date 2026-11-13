# 수동 실행 도구

프로젝트 루트에서 모듈로 실행합니다.

- `inspect/square/`: Square API 응답을 조회·출력합니다. Square 자격증명과 네트워크가 필요합니다.
- `manual/square/`: 실제 Square Sandbox 객체를 생성하고 원본 CSV를 갱신하는 기존 수동 연동 확인 코드입니다. 자동 테스트가 아니며 import만 해도 실행될 수 있습니다. 필요한 입력과 대상 데이터를 먼저 확인하세요.

```bash
python -m scripts.inspect.square.inspect_orders
python -m scripts.manual.square.create_orders
```

자동 구조 검사는 외부 API나 DB 연결 없이 실행할 수 있습니다.

```bash
python -m unittest discover -s tests -v
```

폴더 구조와 모든 이전/새 경로는 `docs/REPOSITORY_STRUCTURE_KO.md`를 참고하세요.
