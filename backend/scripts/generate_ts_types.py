from pydantic2ts import generate_typescript_defs


def main():
    generate_typescript_defs("planned.objects", "../frontend/src/types/api.ts")


if __name__ == "__main__":
    main()
