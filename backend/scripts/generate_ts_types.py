from pydantic2ts import generate_typescript_defs


def main():
    generate_typescript_defs("planned.domain.entities", "../frontend/src/types/api.ts")


if __name__ == "__main__":
    main()
