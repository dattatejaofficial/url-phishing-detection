from dataclasses import dataclass

@dataclass
class DataPreparationArtifact:
    processed_data_path : str
    processed_column_name : str
    target_column_name : str

@dataclass
class FeatureExtractionArtifact:
    features_data_path : str