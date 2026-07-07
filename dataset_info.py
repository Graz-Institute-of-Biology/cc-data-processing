# dataset_registration.py

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
import subprocess
import pkg_resources
from typing import List, Dict
import wandb
from PIL import Image
import tqdm


class DatasetInfo:
    """Tracks dataset metadata for reproducibility and version control."""
    
    KEY_PACKAGES = ['Pillow', 'opencv-python', 'numpy', 'patchify', 
                    'albumentations', 'scikit-image']
    
    def __init__(self, folder_path: str, description: str,
                    ontology_file: str, wandb_project: str,
                    num_images: int = None):
        """
        Initialize dataset info and compute metadata.
        
        Args:
            folder_path: Path to DS_v_xy folder containing images/ and masks/
            version: Manual version string (e.g., 'v12')
            description: Description of dataset changes
            num_original_images: Number of original full-size images
            ontology_file: Path to JSON file containing class names
            wandb_project: WandB project name for artifact upload
        """
        self.folder_path = Path(folder_path)
        self.description = description
        self.ontology_file = ontology_file
        self.wandb_project = wandb_project
        if num_images is not None:
            self.num_original_images = num_images
        else:
            self.num_original_images = self._count_images(self.folder_path / 'imgs')
        # Auto-computed fields
        self.creation_date = datetime.now().isoformat()
        self.classes = self._get_classes_from_ontology()
        self.num_patches = self._count_images(self.folder_path / 'partial_images')
        self.patch_size = self._get_patch_size()
        self.version = self._get_version()
        self.images_hash = self._compute_folder_hash(self.folder_path / 'partial_images')
        self.masks_hash = self._compute_folder_hash(self.folder_path / 'partial_masks')
        self.code_version = self._get_git_commit()
        self.key_packages = self._get_key_packages()
        self._create_lib_snapshot()

        
    def _count_images(self, folder) -> int:
        """Count number of image patches."""
        return len(list(folder.glob('*')))
    
    def _get_version(self) -> str:
        """Generate version string based on folder name.
        Folder name format: dataset_vX_Y_description with X being major and Y minor version.
        """
        major = self.folder_path.name.split('v')[1].split('_')[0]
        minor = self.folder_path.name.split('v')[1].split('_')[1]

        if self.ontology_file == "ontology_atto.json":
            if int(major) >= 11:
                forest_type = self.folder_path.name.split('_')[3]
                sub_type = "_" + forest_type
            else:
                sub_type = ""
        else:
            sub_type = ""

        return f"v{major}.{minor}{sub_type}"
    
    def _get_classes_from_ontology(self) -> List[str]:
        """Extract class names from ontology JSON file."""
        
        with open(self.ontology_file, 'r') as f:
            ontology_data = json.load(f)
        
        classes = list(ontology_data["ontology"].keys())
        return classes
    
    def _create_lib_snapshot(self) -> None:
        """Create lib_snapshot.txt with pip freeze output."""
        snapshot_path = self.folder_path / 'lib_snapshot.txt'
        with open(snapshot_path, 'w') as f:
            subprocess.run(['pip', 'freeze'], stdout=f, check=True)
        print(f"Saved lib_snapshot.txt to {snapshot_path}")

    def _get_patch_size(self) -> int:
        """Determine patch size from first image."""
        images_dir = self.folder_path / 'partial_images'
        first_image = next(images_dir.glob('*'))
        img = Image.open(first_image)
        return img.size[0]  # Assuming square patches
    
    def _compute_folder_hash(self, folder: Path) -> str:
        """Compute SHA256 hash of all files in folder."""

        print(f"Computing hash for folder: {folder}")
        hasher = hashlib.sha256()
        
        for file_path in tqdm.tqdm(sorted(folder.glob('*')), desc="Computing folder hash"):
            if file_path.is_file():
                with open(file_path, 'rb') as f:
                    hasher.update(f.read())

        return hasher.hexdigest()
    
    def _get_git_commit(self) -> str:
        """Get current git commit hash."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()[:7]  # Short hash
        except subprocess.CalledProcessError:
            return "unknown"
    
    def _get_key_packages(self) -> Dict[str, str]:
        """Get versions of key packages."""
        versions = {}
        for package in self.KEY_PACKAGES:
            try:
                version = pkg_resources.get_distribution(package).version
                versions[package] = version
            except pkg_resources.DistributionNotFound:
                versions[package] = "not installed"
        return versions
    
    def to_dict(self,json_dump=False) -> dict:
        """Convert to dictionary for JSON serialization."""
        meta_data = {
            'version': self.version,
            'description': self.description,
            'creation_date': self.creation_date,
            'patch_size': self.patch_size,
            'num_original_images': self.num_original_images,
            'num_patches': self.num_patches,
            'classes': self.classes,
            'images_hash': self.images_hash,
            'masks_hash': self.masks_hash,
            'code_version': self.code_version,
            'key_packages': self.key_packages,
            'ontology_file': self.ontology_file,
            'wandb_project': self.wandb_project,
        }

        if json_dump:
            meta_data['logged_artifact'] = self.logged_artifact.name
            meta_data['qualified_name'] = self.qualified_name

        return meta_data

    def save_json(self) -> None:
        """Save dataset_info.json to dataset folder."""
        json_path = self.folder_path / 'dataset_info.json'

        if json_path.exists():
            os.remove(json_path)

        with open(json_path, 'x') as f:
            json.dump(self.to_dict(json_dump=True), indent=2, fp=f)
        print(f"Saved dataset_info.json to {json_path}")
    
    def upload_to_wandb(self) -> None:
        """Upload dataset as WandB artifact."""
        wandb.init(project=self.wandb_project, job_type='dataset-registration')

        artifact = wandb.Artifact(
            name=f'dataset-{self.version}',
            type='dataset',
            description=self.description,
            metadata=self.to_dict()
        )
        
        # add files
        artifact.add_file(str(self.folder_path / 'lib_snapshot.txt'))
        
        self.logged_artifact = wandb.log_artifact(artifact)
        self.logged_artifact.wait()
        wandb.finish()
        print(f"Uploaded {self.version} to WandB project '{self.wandb_project}'")

        # after uploading store artifact qualified name 
        self.qualified_name = self.logged_artifact.qualified_name



if __name__ == '__main__':
    # Example usage for registering old datasets
    # folder_path = r'C:\Users\faulhamm\Documents\Philipp\training\datasets\ATTO\dataset_v16_0_mixed_increased'
    # folder_path = r'C:\Users\faulhamm\Documents\Philipp\training\datasets\ATTO\dataset_v0_0_mixed_debugging'
    folder_path = r'C:\Users\faulhamm\Documents\Philipp\training\grossglockner\saved_datasets\dataset_v10_0_gg'

    dataset_info = DatasetInfo(
        folder_path=folder_path,
        description='Increased dataset (211 original images) to increase validation set size',
        ontology_file="ontology_gg.json", # "atto", "fbground", "gg", "graz" , "graz_detailed"
        wandb_project='GG' # "ATTO", "GG", "fbground"
    )
    
    dataset_info.upload_to_wandb()
    dataset_info.save_json()
