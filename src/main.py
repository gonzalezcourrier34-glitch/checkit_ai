"""Point d'entrée principal du projet CheckIt.AI."""

from config.paths import ensure_project_directories
from src.pipelines.pipeline import run_pipeline


def main() -> None:
    """Prépare l'environnement local puis lance le pipeline."""

    # Crée les dossiers data, logs, images, temp et lots
    # uniquement au démarrage réel de l'application.
    ensure_project_directories()

    run_pipeline()


if __name__ == "__main__":
    main()