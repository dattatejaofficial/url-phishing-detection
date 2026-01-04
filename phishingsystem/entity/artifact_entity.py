from dataclasses import dataclass

@dataclass
class DataPreparationArtifact:
    processed_data_path : str
    processed_column_name : str
    target_column_name : str

@dataclass
class FeatureExtractionArtifact:
    features_data_path : str

@dataclass
class DataValidationArtifact:
    validated_data_path : str
    validation_report_path : str
    validation_status : str

@dataclass
class DataPersistanceArtifact:
    imported_data_path : str
    validated_data_path : str

@dataclass
class DataEnvelopArtifact:
    data_validation_artifact : DataValidationArtifact
    data_persistance_artifact : DataPersistanceArtifact

@dataclass
class DataTransformationArtifact:
    train_data_path : str
    test_data_path : str