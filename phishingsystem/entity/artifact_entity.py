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

@dataclass
class ModelTrainerArtifact:
    model_uri : str
    registered_model_name : str
    model_version : str
    model_tracking_uri : str
    test_data_probs_path : str
    test_data_path : str

@dataclass
class ModelEvaluationArtifact:
    model_uri : str
    registered_model_name : str
    model_version : str
    model_tracking_uri : str
    evaluation_report_path : str
    threshold : float

@dataclass
class ModelFinalizerArtifact:
    model_name : str
    model_version : str
    stage : str
    threshold : float
    run_id : str