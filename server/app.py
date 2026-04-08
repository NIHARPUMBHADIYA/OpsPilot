from main import app
import uvicorn


def main() -> None:
    """Run the FastAPI application with Uvicorn."""
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
