#!/usr/bin/env python
import os
import sys


def main() -> None:
  """
  Ponto de entrada para comandos de administração do Django.
  Usa o módulo de settings principal do projeto (`core.settings`).
  """
  os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
  try:
    from django.core.management import execute_from_command_line
  except ImportError as exc:
    raise ImportError(
      "Não foi possível importar Django. "
      "Verifique se ele está instalado e disponível no seu PYTHONPATH, "
      "e se o ambiente virtual está correto."
    ) from exc
  execute_from_command_line(sys.argv)


if __name__ == "__main__":
  main()
