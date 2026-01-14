import os
import sys

from phishingsystem.logging.logger import logging
from phishingsystem.exception.exception import PhishingSystemException

from phishingsystem.entity.config_entity import FeatureExtractionConfig
from phishingsystem.entity.artifact_entity import DataPreparationArtifact, FeatureExtractionArtifact

from phishingsystem.utils.url_preparation.url_feature_extraction import URLFeaturesExtraction
from phishingsystem.utils.main_utils import read_csv_file

import pandas as pd

class FeatureExtraction:
    def __init__(self, data_preparation_artifact : DataPreparationArtifact, feature_extraction_config : FeatureExtractionConfig):
        self.data_preparation_artifact = data_preparation_artifact
        self.feature_extraction_config = feature_extraction_config
    
    def initiate_feature_extraction(self):
        try:
            logging.info('Initiating Feature Extraction')

            processed_data = read_csv_file(self.data_preparation_artifact.processed_data_path)
            url_col = self.data_preparation_artifact.processed_column_name

            features_dict = processed_data[url_col].apply(lambda url: URLFeaturesExtraction(url).extract_features())
            logging.info('Extracted features from the URLs')

            features_df = pd.DataFrame(features_dict.tolist())
            target_col = self.data_preparation_artifact.target_column_name
            features_df[target_col] = processed_data[target_col]

            features_data_path = self.feature_extraction_config.features_data_path
            dir_path = os.path.dirname(features_data_path)
            os.makedirs(dir_path, exist_ok=True)

            features_df = features_df.drop_duplicates(ignore_index=True)
            features_df.to_csv(features_data_path,index=False,header=True)
            logging.info('Saved the features data')

            feature_extraction_artifact = FeatureExtractionArtifact(
                features_data_path = features_data_path
            )

            logging.info('Completed feature extraction')
            return feature_extraction_artifact

        except Exception as e:
            raise PhishingSystemException(e,sys)