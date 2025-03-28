################### test.py

import os
import re
import json
import traceback

class UnitySceneParser:
    def __init__(self):
        # Comprehensive component type mapping
        self.component_map = {
            # Core Components
    '0': {'name': 'Object', 'category': 'Core'},
    '1': {'name': 'GameObject', 'category': 'Core'},
    '2': {'name': 'Component', 'category': 'Core'},
    '4': {'name': 'Transform', 'category': 'Core'},
    '8': {'name': 'Behaviour', 'category': 'Core'},
    '114': {'name': 'MonoBehaviour', 'category': 'Scripting'},
    '115': {'name': 'MonoScript', 'category': 'Scripting'},

    # Managers
    '3': {'name': 'LevelGameManager', 'category': 'Management'},
    '5': {'name': 'TimeManager', 'category': 'Management'},
    '6': {'name': 'GlobalGameManager', 'category': 'Management'},
    '9': {'name': 'GameManager', 'category': 'Management'},
    '11': {'name': 'AudioManager', 'category': 'Management'},
    '13': {'name': 'InputManager', 'category': 'Management'},
    '19': {'name': 'Physics2DSettings', 'category': 'Management'},
    '30': {'name': 'GraphicsSettings', 'category': 'Management'},
    '55': {'name': 'PhysicsManager', 'category': 'Management'},
    '78': {'name': 'TagManager', 'category': 'Management'},
    '129': {'name': 'PlayerSettings', 'category': 'Management'},
    '141': {'name': 'BuildSettings', 'category': 'Management'},
    '147': {'name': 'ResourceManager', 'category': 'Management'},
    '196': {'name': 'NavMeshSettings', 'category': 'Management'},

    # Physics Components
    '50': {'name': 'Rigidbody2D', 'category': 'Physics'},
    '53': {'name': 'Collider2D', 'category': 'Physics'}, # Base class
    '54': {'name': 'Rigidbody', 'category': 'Physics'},
    '56': {'name': 'Collider', 'category': 'Physics'}, # Base class
    '58': {'name': 'CircleCollider2D', 'category': 'Physics'},
    '59': {'name': 'HingeJoint', 'category': 'Physics'},
    '60': {'name': 'PolygonCollider2D', 'category': 'Physics'},
    '61': {'name': 'BoxCollider2D', 'category': 'Physics'},
    '62': {'name': 'PhysicsMaterial2D', 'category': 'Physics'},
    '64': {'name': 'MeshCollider', 'category': 'Physics'},
    '65': {'name': 'BoxCollider', 'category': 'Physics'},
    '68': {'name': 'EdgeCollider2D', 'category': 'Physics'},
    '70': {'name': 'CapsuleCollider2D', 'category': 'Physics'},
    '72': {'name': 'ComputeShader', 'category': 'Shader'},
    '146': {'name': 'WheelCollider', 'category': 'Physics'},
    '153': {'name': 'ConfigurableJoint', 'category': 'Physics'},
    '154': {'name': 'TerrainCollider', 'category': 'Physics'},
    '156': {'name': 'TerrainData', 'category': 'Terrain'},

    # Rendering Components
    '20': {'name': 'Camera', 'category': 'Rendering'},
    '21': {'name': 'Material', 'category': 'Rendering'},
    '23': {'name': 'MeshRenderer', 'category': 'Rendering'},
    '25': {'name': 'Renderer', 'category': 'Rendering'}, # Base class
    '27': {'name': 'Texture', 'category': 'Rendering'}, # Base class
    '28': {'name': 'Texture2D', 'category': 'Rendering'},
    '33': {'name': 'MeshFilter', 'category': 'Rendering'},
    '43': {'name': 'Mesh', 'category': 'Rendering'},
    '45': {'name': 'Skybox', 'category': 'Rendering'},
    '47': {'name': 'QualitySettings', 'category': 'Management'}, # Also Rendering settings
    '48': {'name': 'Shader', 'category': 'Rendering'},
    '49': {'name': 'TextAsset', 'category': 'Asset'}, # Data asset
    '84': {'name': 'RenderTexture', 'category': 'Rendering'},
    '89': {'name': 'Cubemap', 'category': 'Rendering'},
    '95': {'name': 'Animator', 'category': 'Animation'}, # Animation system
    '102': {'name': 'LODGroup', 'category': 'Rendering'},
    '111': {'name': 'Animation', 'category': 'Animation'}, # Legacy Animation
    '126': {'name': 'LightmapSettings', 'category': 'Rendering'}, # Scene settings
    '157': {'name': 'LightProbeGroup', 'category': 'Rendering'},
    '258': {'name': 'LightProbeProxyVolume', 'category': 'Rendering'},
    '104': {'name': 'Light', 'category': 'Rendering'},
    '108': {'name': 'LightProbes', 'category': 'Rendering'},
    '109': {'name': 'LightingDataAsset', 'category': 'Rendering'},
    '110': {'name': 'LightmapParameters', 'category': 'Rendering'},
    '205': {'name': 'LightAnchor', 'category': 'Rendering'}, # Internal? Related to Light Probes

    # Audio Components
    '81': {'name': 'AudioListener', 'category': 'Audio'},
    '82': {'name': 'AudioSource', 'category': 'Audio'},
    '83': {'name': 'AudioClip', 'category': 'Audio'},
    '164': {'name': 'AudioReverbFilter', 'category': 'Audio'},
    '165': {'name': 'AudioHighPassFilter', 'category': 'Audio'},
    '166': {'name': 'AudioChorusFilter', 'category': 'Audio'},
    '167': {'name': 'AudioReverbZone', 'category': 'Audio'},
    '168': {'name': 'AudioEchoFilter', 'category': 'Audio'},
    '169': {'name': 'AudioLowPassFilter', 'category': 'Audio'},
    '170': {'name': 'AudioDistortionFilter', 'category': 'Audio'},
    '180': {'name': 'AudioBehaviour', 'category': 'Audio'}, # Base class?
    '181': {'name': 'AudioFilter', 'category': 'Audio'}, # Base class?

    # UI Components
    '128': {'name': 'Font', 'category': 'UI'},
    '222': {'name': 'Canvas', 'category': 'UI'},
    '223': {'name': 'CanvasRenderer', 'category': 'UI'},
    '224': {'name': 'RectTransform', 'category': 'UI'}, # Already included from continuation
    '225': {'name': 'CanvasGroup', 'category': 'UI'}, # Already included from continuation
    '226': {'name': 'SpriteRenderer', 'category': 'Rendering'}, # Often used in UI, but fundamentally rendering
    # UI Components (already covered/refined in initial_map)
    '224': {'name': 'RectTransform', 'category': 'UI'},
    '225': {'name': 'CanvasGroup', 'category': 'UI'},
    '226': {'name': 'SpriteRenderer', 'category': 'UI'}, # Corrected category above

    # Animation Components
    '74': {'name': 'AnimationClip', 'category': 'Animation'},
    '95': {'name': 'Animator', 'category': 'Animation'}, # Already in initial_map
    '111': {'name': 'Animation', 'category': 'Animation'}, # Already in initial_map
    '320': {'name': 'AnimatorOverrideController', 'category': 'Animation'},
    '319': {'name': 'RuntimeAnimatorController', 'category': 'Animation'},
    '168': {'name': 'Avatar', 'category': 'Animation'}, # From Miscellaneous
    '169': {'name': 'AnimatorController', 'category': 'Animation'}, # From Miscellaneous - likely RuntimeAnimatorController asset or similar

    # Effects Components (Some Obsolete)
    '12': {'name': 'ParticleAnimator', 'category': 'Effects'}, # Obsolete
    '15': {'name': 'EllipsoidParticleEmitter', 'category': 'Effects'}, # Obsolete
    '17': {'name': 'Pipeline', 'category': 'Asset'}, # Likely Render Pipeline Asset
    '26': {'name': 'ParticleRenderer', 'category': 'Effects'}, # Obsolete
    '86': {'name': 'CustomRenderTexture', 'category': 'Rendering'},
    '87': {'name': 'MeshParticleEmitter', 'category': 'Effects'}, # Obsolete
    '88': {'name': 'ParticleEmitter', 'category': 'Effects'}, # Obsolete
    '90': {'name': 'LODGroup', 'category': 'Rendering'}, # Duplicate ID 102 exists and is preferred
    '248': {'name': 'VFXRenderer', 'category': 'Effects'}, # Visual Effects Graph

    # Navigation Components
    '195': {'name': 'NavMeshAgent', 'category': 'Navigation'},
    '196': {'name': 'NavMeshSettings', 'category': 'Management'}, # Already in initial_map
    '197': {'name': 'NavMeshObstacle', 'category': 'Navigation'},

    # Networking Components (Legacy/Obsolete)
    '102': {'name': 'NetworkManager', 'category': 'Networking'}, # ID 102 used by LODGroup, omitting this legacy entry
    '103': {'name': 'NetworkView', 'category': 'Networking'}, # Obsolete UNET/Legacy

    # Miscellaneous / Core / Editor / Assets / Potential Duplicates
    '31': {'name': 'OcclusionCullingSettings', 'category': 'Rendering'}, # Scene settings
    '41': {'name': 'OcclusionPortal', 'category': 'Rendering'},
    '92': {'name': 'FlareLayer', 'category': 'Rendering'},
    '104': {'name': 'HaloManager', 'category': 'Rendering'}, # ID 104 used by Light, omitting this
    '120': {'name': 'AssetBundle', 'category': 'Core'}, # Asset Management
    '121': {'name': 'AssetBundleManifest', 'category': 'Core'}, # Asset Management
    '122': {'name': 'ScriptMapper', 'category': 'Miscellaneous'}, # Internal?
    '123': {'name': 'DelayedCallManager', 'category': 'Miscellaneous'}, # Internal?
    '124': {'name': 'TextMesh', 'category': 'UI'}, # Legacy Text
    '125': {'name': 'RenderSettings', 'category': 'Rendering'}, # Scene settings
    '127': {'name': 'LightmapSettings', 'category': 'Rendering'}, # ID 126 exists and is preferred
    '130': {'name': 'BuildSettings', 'category': 'Management'}, # ID 141 exists and is preferred
    '131': {'name': 'AssetDatabase', 'category': 'Editor'}, # Editor-only class
    '132': {'name': 'AudioMixer', 'category': 'Audio'},
    '133': {'name': 'AudioMixerController', 'category': 'Audio'}, # Internal?
    '134': {'name': 'AudioMixerGroupController', 'category': 'Audio'}, # Internal?
    '135': {'name': 'AudioMixerEffectController', 'category': 'Audio'}, # Internal?
    '136': {'name': 'AudioMixerSnapshotController', 'category': 'Audio'}, # Internal?
    '137': {'name': 'Physics2DManager', 'category': 'Management'}, # Duplicate of Physics2DSettings? (ID 19) Keeping this as potentially distinct internal manager.
    '138': {'name': 'PhysicsManager', 'category': 'Management'}, # ID 55 exists and is preferred
    '139': {'name': 'TimeManager', 'category': 'Management'}, # ID 5 exists and is preferred
    '140': {'name': 'AudioManager', 'category': 'Management'}, # ID 11 exists and is preferred
    '141': {'name': 'InputManager', 'category': 'Management'}, # ID 13 exists and is preferred (BuildSettings is 141)
    '142': {'name': 'MeshRenderer', 'category': 'Rendering'}, # ID 23 exists and is preferred
    '143': {'name': 'GraphicsSettings', 'category': 'Management'}, # ID 30 exists and is preferred
    '144': {'name': 'QualitySettings', 'category': 'Management'}, # ID 47 exists and is preferred
    '145': {'name': 'Shader', 'category': 'Rendering'}, # ID 48 exists and is preferred
    '146': {'name': 'TextAsset', 'category': 'Asset'}, # ID 49 exists and is preferred (WheelCollider is 146)
    '147': {'name': 'Rigidbody2D', 'category': 'Physics'}, # ID 50 exists and is preferred (ResourceManager is 147)
    '148': {'name': 'PhysicsMaterial2D', 'category': 'Physics'}, # ID 62 exists and is preferred
    '149': {'name': 'MeshCollider', 'category': 'Physics'}, # ID 64 exists and is preferred
    '150': {'name': 'BoxCollider', 'category': 'Physics'}, # ID 65 exists and is preferred
    '151': {'name': 'SpriteCollider2D', 'category': 'Physics'},
    '152': {'name': 'EdgeCollider2D', 'category': 'Physics'}, # ID 68 exists and is preferred
    '154': {'name': 'CapsuleCollider2D', 'category': 'Physics'}, # ID 70 exists and is preferred (TerrainCollider is 154)
    '155': {'name': 'ComputeShader', 'category': 'Shader'}, # ID 72 exists and is preferred
    '158': {'name': 'ConstantForce', 'category': 'Physics'},
    '159': {'name': 'WorldParticleCollider', 'category': 'Physics'}, # Obsolete
    '160': {'name': 'TagManager', 'category': 'Management'}, # ID 78 exists and is preferred
    '161': {'name': 'AudioListener', 'category': 'Audio'}, # ID 81 exists and is preferred
    '162': {'name': 'AudioSource', 'category': 'Audio'}, # ID 82 exists and is preferred
    '163': {'name': 'AudioClip', 'category': 'Audio'}, # ID 83 exists and is preferred
    '164': {'name': 'RenderTexture', 'category': 'Rendering'}, # ID 84 exists and is preferred (AudioReverbFilter is 164)
    '165': {'name': 'MeshParticleEmitter', 'category': 'Effects'}, # ID 87 exists and is preferred (AudioHighPassFilter is 165)
    '166': {'name': 'ParticleEmitter', 'category': 'Effects'}, # ID 88 exists and is preferred (AudioChorusFilter is 166)
    '167': {'name': 'Cubemap', 'category': 'Rendering'}, # ID 89 exists and is preferred (AudioReverbZone is 167)
    '170': {'name': 'GUILayer', 'category': 'UI'}, # Legacy UI, ID 170 is AudioDistortionFilter
    '171': {'name': 'RuntimeAnimatorController', 'category': 'Animation'}, # ID 319 exists and is preferred
    '172': {'name': 'ScriptMapper', 'category': 'Miscellaneous'}, # ID 122 exists and is preferred
    '173': {'name': 'DelayedCallManager', 'category': 'Miscellaneous'}, # ID 123 exists and is preferred
    '174': {'name': 'TextMesh', 'category': 'UI'}, # ID 124 exists and is preferred
    '175': {'name': 'RenderSettings', 'category': 'Rendering'}, # ID 125 exists and is preferred
    '176': {'name': 'LightmapSettings', 'category': 'Rendering'}, # ID 126 exists and is preferred
    }

    def parse_scene(self, file_path):
        """
        Comprehensive parsing of Unity scene file
        """
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as file:
                content = file.read()
            
            # Initialize scene details dictionary
            scene_details = {
                'file_name': os.path.basename(file_path),
                'total_objects': 0,
                'objects': {}
            }
            
            # More robust entry parsing
            entries = re.findall(r'--- !u!(\d+) &(\d+)\n(.*?)(?=--- !u!|\Z)', content, re.DOTALL | re.MULTILINE)
            
            # Track game objects to ensure we capture all components
            game_objects = {}
            
            # First pass: Collect all GameObjects
            for entry_type, entry_id, entry_content in entries:
                if entry_type == '1':  # GameObject
                    name_match = re.search(r'm_Name: (.*?)\n', entry_content)
                    name = name_match.group(1).strip() if name_match else f'GameObject_{entry_id}'
                    
                    game_objects[entry_id] = {
                        'name': name,
                        'entry_id': entry_id,
                        'components': []
                    }
            
            # Second pass: Parse components and associate with GameObjects
            for entry_type, entry_id, entry_content in entries:
                # Find associated GameObject
                go_match = re.search(r'm_GameObject: {fileID: (\d+)}', entry_content)
                if go_match:
                    go_id = go_match.group(1)
                    
                    # Ensure GameObject exists
                    if go_id in game_objects:
                        # Get component information
                        component_info = self.component_map.get(entry_type, 
                            {'name': f'Unknown Component ({entry_type})', 'category': 'Miscellaneous'})
                        
                        # Parse specific component details
                        component_details = self._parse_component_details(entry_type, entry_content)
                        
                        # Combine component info
                        full_component = {
                            'type': component_info['name'],
                            'category': component_info['category'],
                            **component_details
                        }
                        
                        # Add to GameObject's components
                        game_objects[go_id]['components'].append(full_component)
            
            # Transfer to scene details, filtering out empty objects
            for go_id, obj_data in game_objects.items():
                if obj_data['components']:  # Only add objects with components
                    scene_details['objects'][obj_data['name']] = obj_data
            
            scene_details['total_objects'] = len(scene_details['objects'])
            
            return scene_details
        
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            traceback.print_exc()
            return {}

    def _parse_component_details(self, component_type, content):
        """
        Parse detailed information for different component types
        """
        details = {}
        
        # Specific component type parsing
        if component_type == '25':  # Renderer details
            details = {
                'cast_shadows': self._extract_bool(r'm_CastShadows: (\d+)', content),
                'receive_shadows': self._extract_bool(r'm_ReceiveShadows: (\d+)', content)
            }
        
        # MeshFilter details
        elif component_type == '33':
            details = {
                'mesh_file_id': self._extract_int(r'm_Mesh: {fileID: (\d+)}', content)
            }
        
        # Rigidbody details
        elif component_type == '54':
            details = {
                'mass': self._extract_float(r'm_Mass: ([\d.]+)', content),
                'use_gravity': self._extract_bool(r'm_UseGravity: (\d)', content),
                'is_kinematic': self._extract_bool(r'm_IsKinematic: (\d)', content),
                'interpolation': self._map_interpolation(self._extract_int(r'm_Interpolate: (\d)', content)),
                'collision_detection': self._map_collision_detection(self._extract_int(r'm_CollisionDetection: (\d)', content))
            }
        
        # Collider details
        elif component_type in ['64', '65', '153']:
            details = {
                'center': self._extract_vector3(r'm_Center: {x: ([\d.-]+), y: ([\d.-]+), z: ([\d.-]+)}', content),
                'size': self._extract_vector3(r'm_Size: {x: ([\d.-]+), y: ([\d.-]+), z: ([\d.-]+)}', content) if component_type == '65' else None,
                'radius': self._extract_float(r'm_Radius: ([\d.]+)', content) if component_type == '64' else None,
                'convex': self._extract_bool(r'm_Convex: (\d)', content) if component_type == '64' else None
            }
        
        # Camera details
        elif component_type == '20':
            details = {
                'field_of_view': self._extract_float(r'm_FieldOfView: ([\d.]+)', content),
                'near_clip_plane': self._extract_float(r'm_NearClipPlane: ([\d.]+)', content),
                'far_clip_plane': self._extract_float(r'm_FarClipPlane: ([\d.]+)', content),
                'background_color': self._extract_color(r'm_BackGroundColor: {r: ([\d.]+), g: ([\d.]+), b: ([\d.]+), a: ([\d.]+)}', content)
            }
        
        # Transform details
        elif component_type == '4':
            details = {
                'local_position': self._extract_vector3(r'm_LocalPosition: {x: ([\d.-]+), y: ([\d.-]+), z: ([\d.-]+)}', content),
                'local_rotation': self._extract_vector4(r'm_LocalRotation: {x: ([\d.-]+), y: ([\d.-]+), z: ([\d.-]+), w: ([\d.-]+)}', content),
                'local_scale': self._extract_vector3(r'm_LocalScale: {x: ([\d.-]+), y: ([\d.-]+), z: ([\d.-]+)}', content)
            }
        
        # Light details
        elif component_type == '104':
            details = {
                'light_type': self._map_light_type(self._extract_int(r'm_Type: (\d+)', content)),
                'color': self._extract_color(r'm_Color: {r: ([\d.]+), g: ([\d.]+), b: ([\d.]+), a: ([\d.]+)}', content),
                'intensity': self._extract_float(r'm_Intensity: ([\d.]+)', content),
                'range': self._extract_float(r'm_Range: ([\d.]+)', content)
            }
        
        # Generic component fallback
        else:
            details = {
                'raw_content_preview': content[:200]  # First 200 chars for context
            }
        
        return details

    def _extract_vector3(self, pattern, content):
        """Extract Vector3 from content"""
        match = re.search(pattern, content)
        return {
            'x': float(match.group(1)) if match else 0.0,
            'y': float(match.group(2)) if match else 0.0,
            'z': float(match.group(3)) if match else 0.0
        } if match else None

    def _extract_vector4(self, pattern, content):
        """Extract Vector4 (Quaternion) from content"""
        match = re.search(pattern, content)
        return {
            'x': float(match.group(1)) if match else 0.0,
            'y': float(match.group(2)) if match else 0.0,
            'z': float(match.group(3)) if match else 0.0,
            'w': float(match.group(4)) if match else 1.0
        } if match else None

    def _extract_color(self, pattern, content):
        """Extract color from content"""
        match = re.search(pattern, content)
        return {
            'r': float(match.group(1)) if match else 0.0,
            'g': float(match.group(2)) if match else 0.0,
            'b': float(match.group(3)) if match else 0.0,
            'a': float(match.group(4)) if match else 1.0
        } if match else None

    def _extract_float(self, pattern, content, default=0.0):
        """Extract float value from content"""
        match = re.search(pattern, content)
        return float(match.group(1)) if match else default

    def _extract_bool(self, pattern, content, default=False):
        """Extract boolean value from content"""
        match = re.search(pattern, content)
        return bool(int(match.group(1))) if match else default

    def _extract_int(self, pattern, content, default=0):
        """Extract integer value from content"""
        match = re.search(pattern, content)
        return int(match.group(1)) if match else default

    def _map_interpolation(self, value):
        """Map Rigidbody interpolation values"""
        interpolation_map = {0: 'None', 1: 'Interpolate', 2: 'Extrapolate'}
        return interpolation_map.get(value, 'Unknown')

    def _map_collision_detection(self, value):
        """Map Rigidbody collision detection values"""
        collision_map = {0: 'Discrete', 1: 'Continuous', 2: 'Continuous Dynamic'}
        return collision_map.get(value, 'Unknown')

    def _map_light_type(self, value):
        """Map Light type values"""
        light_type_map = {0: 'Spot', 1: 'Directional', 2: 'Point', 3: 'Area'}
        return light_type_map.get(value, 'Unknown')

def comprehensive_scene_analysis(project_path):
    """
    Perform comprehensive analysis of Unity scenes
    
    Args:
        project_path (str): Path to the Unity project directory
    
    Returns:
        dict: Comprehensive analysis of Unity scenes with details about scenes, objects, and components
    """
    # Initialize parser
    parser = UnitySceneParser()
    
    # Collect scene information
    scene_analysis = {
        'total_scenes': 0,
        'total_objects': 0,
        'component_breakdown': {},
        'scenes': {}
    }
    
    # Walk through project searching for scene files
    for root, _, files in os.walk(os.path.join(project_path, "Assets")):
        for file in files:
            if file.endswith(".unity"):
                file_path = os.path.join(root, file)
                
                # Parse scene
                scene_details = parser.parse_scene(file_path)
                
                # Update scene analysis
                scene_analysis['total_scenes'] += 1
                scene_analysis['total_objects'] += scene_details.get('total_objects', 0)
                scene_analysis['scenes'][scene_details['file_name']] = scene_details
                
                # Component breakdown
                for obj_name, obj_data in scene_details.get('objects', {}).items():
                    for component in obj_data.get('components', []):
                        comp_type = component.get('type', 'Unknown')
                        scene_analysis['component_breakdown'][comp_type] = scene_analysis['component_breakdown'].get(comp_type, 0) + 1
    
    # Optional: Save detailed JSON report
    # with open('unity_scene_analysis.json', 'w') as f:
    #     json.dump(scene_analysis, f, indent=2)
    
    return scene_analysis

def main():
    # Replace with your Unity project folder path
    unity_project_path = r"C:/Users/user/My project (3)"
    print(comprehensive_scene_analysis(unity_project_path))
