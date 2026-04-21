from pathlib import Path

import pandas as pd
from django.conf import settings
from django.test import TestCase
from django.urls import reverse


class ProcessedDataIntegrityTests(TestCase):
	required_files = {
		"severidad_region.csv": ["codregion", "REGION", "total", "alta"],
		"severidad_comuna.csv": ["codregion", "cod_comuna", "COMUNA_GEOJSON", "total", "alta"],
		"hospitales.csv": ["COD_HOSPITAL", "NOMBRE_HOSPITAL", "total"],
		"traslados.csv": ["cantidad"],
		"motivo_traslado.csv": ["cod_hospital", "diagnostico"],
	}

	traslados_alternative_pairs = [
		("cod_origen", "cod_destino"),
		("cod_hospital_origen", "cod_hospital_destino"),
	]

	@property
	def processed_dir(self) -> Path:
		return Path(settings.DATA_DIR)

	def test_required_processed_files_exist(self) -> None:
		for file_name in self.required_files:
			with self.subTest(file=file_name):
				self.assertTrue(
					(self.processed_dir / file_name).exists(),
					msg=f"Falta archivo procesado obligatorio: {file_name}",
				)

	def test_required_columns_present(self) -> None:
		for file_name, expected_columns in self.required_files.items():
			with self.subTest(file=file_name):
				df = pd.read_csv(self.processed_dir / file_name)
				for column in expected_columns:
					self.assertIn(
						column,
						df.columns,
						msg=f"{file_name}: falta columna obligatoria {column}",
					)

	def test_region_totals_are_consistent(self) -> None:
		region_df = pd.read_csv(self.processed_dir / "severidad_region.csv")
		total = pd.to_numeric(region_df["total"], errors="coerce").sum()
		alta = pd.to_numeric(region_df["alta"], errors="coerce").sum()

		self.assertGreater(total, 0, "La suma de total debe ser mayor que 0")
		self.assertGreaterEqual(alta, 0, "La suma de alta no puede ser negativa")
		self.assertLessEqual(alta, total, "La suma de alta no puede superar la suma de total")

	def test_traslados_origin_destination_schema(self) -> None:
		df = pd.read_csv(self.processed_dir / "traslados.csv")
		self.assertTrue(
			any(
				origin in df.columns and destination in df.columns
				for origin, destination in self.traslados_alternative_pairs
			),
			msg=(
				"traslados.csv debe incluir columnas de origen/destino: "
				"cod_origen+cod_destino o cod_hospital_origen+cod_hospital_destino"
			),
		)


class DashboardViewSmokeTests(TestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		processed_dir = Path(settings.DATA_DIR)

		comuna_df = pd.read_csv(processed_dir / "severidad_comuna.csv")
		hospital_df = pd.read_csv(processed_dir / "hospitales.csv")

		cls.codregion = int(pd.to_numeric(comuna_df["codregion"], errors="coerce").dropna().iloc[0])
		cls.cod_comuna = int(pd.to_numeric(comuna_df["cod_comuna"], errors="coerce").dropna().iloc[0])
		cls.cod_hospital = int(pd.to_numeric(hospital_df["COD_HOSPITAL"], errors="coerce").dropna().iloc[0])

	def test_home_renders(self) -> None:
		response = self.client.get(reverse("home"))
		self.assertEqual(response.status_code, 200)
		self.assertIn("regiones_json", response.context)

	def test_api_comunas_contract(self) -> None:
		response = self.client.get(reverse("api_comunas", args=[self.codregion]))
		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertIn("comunas", payload)
		self.assertIn("geojson", payload)
		self.assertIn("hospitales", payload)

	def test_api_traslados_contract(self) -> None:
		response = self.client.get(reverse("api_traslados"))
		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertIn("traslados", payload)

	def test_analisis_region_renders(self) -> None:
		response = self.client.get(reverse("analisis_region", args=[self.codregion]))
		self.assertEqual(response.status_code, 200)
		self.assertIn("encontrado", response.context)

	def test_analisis_comuna_renders(self) -> None:
		response = self.client.get(reverse("analisis_comuna", args=[self.cod_comuna]))
		self.assertEqual(response.status_code, 200)
		self.assertIn("encontrado", response.context)

	def test_analisis_hospital_renders(self) -> None:
		response = self.client.get(reverse("analisis_hospital", args=[self.cod_hospital]))
		self.assertEqual(response.status_code, 200)
		self.assertIn("encontrado", response.context)

	def test_analisis_pais_renders(self) -> None:
		response = self.client.get(reverse("analisis_pais"))
		self.assertEqual(response.status_code, 200)
		self.assertIn("top_regiones", response.context)

	def test_vista_traslados_renders(self) -> None:
		response = self.client.get(reverse("vista_traslados"))
		self.assertEqual(response.status_code, 200)
		self.assertIn("tabla", response.context)
