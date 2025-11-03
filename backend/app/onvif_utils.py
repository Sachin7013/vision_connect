# onvif_utils.py
"""
ONVIF Camera Discovery and Management
Supports automatic discovery of IP cameras on network
"""
from typing import List, Dict, Optional
from onvif import ONVIFCamera
from wsdiscovery.discovery import ThreadedWSDiscovery as WSDiscovery
from wsdiscovery.scope import Scope
import socket
import re

class ONVIFCameraManager:
    """
    Manages ONVIF camera discovery and communication
    Similar to ONVIF Device Manager functionality
    """
    
    @staticmethod
    def discover_cameras(timeout: int = 5) -> List[Dict]:
        """
        Discover all ONVIF cameras on local network
        Uses WS-Discovery protocol (same as ONVIF Device Manager)
        
        Returns:
            List of discovered cameras with their details
        """
        discovered_cameras = []
        
        try:
            # Start WS-Discovery
            wsd = WSDiscovery()
            wsd.start()
            
            # Search for ONVIF devices
            services = wsd.searchServices(timeout=timeout)
            
            for service in services:
                # Extract camera information
                camera_info = {
                    "xaddrs": [],
                    "scopes": [],
                    "types": []
                }
                
                # Get XAddrs (camera URLs)
                if hasattr(service, 'getXAddrs'):
                    camera_info["xaddrs"] = service.getXAddrs()
                
                # Get Scopes (camera metadata)
                if hasattr(service, 'getScopes'):
                    scopes = service.getScopes()
                    for scope in scopes:
                        scope_value = scope.getValue() if hasattr(scope, 'getValue') else str(scope)
                        camera_info["scopes"].append(scope_value)
                        
                        # Parse common ONVIF scope patterns
                        # onvif://www.onvif.org/name/CameraName
                        # onvif://www.onvif.org/hardware/Model
                        # onvif://www.onvif.org/location/Building1
                        
                        if "name/" in scope_value:
                            camera_info["name"] = scope_value.split("name/")[-1]
                        elif "hardware/" in scope_value:
                            camera_info["hardware"] = scope_value.split("hardware/")[-1]
                        elif "location/" in scope_value:
                            camera_info["location"] = scope_value.split("location/")[-1]
                
                # Get Types
                if hasattr(service, 'getTypes'):
                    camera_info["types"] = [str(t) for t in service.getTypes()]
                
                # Extract IP address from XAddrs
                if camera_info["xaddrs"]:
                    xaddr = camera_info["xaddrs"][0]
                    ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', xaddr)
                    if ip_match:
                        camera_info["ip"] = ip_match.group(1)
                        
                        # Extract port
                        port_match = re.search(r':(\d+)/', xaddr)
                        camera_info["port"] = int(port_match.group(1)) if port_match else 80
                
                # Only add if it has an IP address
                if "ip" in camera_info:
                    discovered_cameras.append({
                        "ip": camera_info.get("ip"),
                        "port": camera_info.get("port", 80),
                        "name": camera_info.get("name", "Unknown Camera"),
                        "hardware": camera_info.get("hardware", "Unknown"),
                        "location": camera_info.get("location", ""),
                        "xaddrs": camera_info.get("xaddrs", []),
                        "manufacturer": ONVIFCameraManager._extract_manufacturer(camera_info)
                    })
            
            wsd.stop()
            
        except Exception as e:
            print(f"Error discovering cameras: {e}")
        
        return discovered_cameras
    
    @staticmethod
    def _extract_manufacturer(camera_info: Dict) -> str:
        """Extract manufacturer from scopes or hardware info"""
        hardware = camera_info.get("hardware", "").lower()
        scopes = " ".join(camera_info.get("scopes", [])).lower()
        
        # Common manufacturers
        manufacturers = {
            "hikvision": "Hikvision",
            "dahua": "Dahua",
            "axis": "Axis",
            "cpplus": "CP Plus",
            "cp-plus": "CP Plus",
            "vivotek": "Vivotek",
            "sony": "Sony",
            "panasonic": "Panasonic",
            "bosch": "Bosch"
        }
        
        for key, name in manufacturers.items():
            if key in hardware or key in scopes:
                return name
        
        return "Generic ONVIF"
    
    @staticmethod
    def connect_camera(ip: str, port: int, username: str, password: str) -> Optional[ONVIFCamera]:
        """
        Connect to ONVIF camera and verify credentials
        
        Args:
            ip: Camera IP address
            port: ONVIF port (usually 80)
            username: Camera username
            password: Camera password
            
        Returns:
            ONVIFCamera object if successful, None otherwise
        """
        try:
            # Create ONVIF camera object
            camera = ONVIFCamera(ip, port, username, password)
            
            # Test connection by getting device info
            device_info = camera.devicemgmt.GetDeviceInformation()
            
            return camera
            
        except Exception as e:
            print(f"Failed to connect to camera {ip}: {e}")
            return None
    
    @staticmethod
    def get_camera_info(camera: ONVIFCamera) -> Dict:
        """
        Get detailed information from connected ONVIF camera
        
        Returns:
            Dictionary with camera details
        """
        try:
            device_mgmt = camera.devicemgmt
            
            # Get device information
            device_info = device_mgmt.GetDeviceInformation()
            
            # Get network interfaces
            network_interfaces = device_mgmt.GetNetworkInterfaces()
            
            # Get system date/time
            system_datetime = device_mgmt.GetSystemDateAndTime()
            
            return {
                "manufacturer": device_info.Manufacturer,
                "model": device_info.Model,
                "firmware_version": device_info.FirmwareVersion,
                "serial_number": device_info.SerialNumber,
                "hardware_id": device_info.HardwareId,
                "network_interfaces": str(network_interfaces),
                "system_datetime": str(system_datetime)
            }
            
        except Exception as e:
            print(f"Error getting camera info: {e}")
            return {}
    
    @staticmethod
    def get_rtsp_url(camera: ONVIFCamera, profile_index: int = 0) -> Optional[str]:
        """
        Get RTSP stream URL from camera
        
        Args:
            camera: Connected ONVIFCamera object
            profile_index: Media profile index (0 = main stream, 1 = sub stream)
            
        Returns:
            RTSP URL string or None
        """
        try:
            # Get media service
            media_service = camera.create_media_service()
            
            # Get available profiles
            profiles = media_service.GetProfiles()
            
            if not profiles:
                return None
            
            # Use specified profile or first available
            profile = profiles[profile_index] if profile_index < len(profiles) else profiles[0]
            
            # Get stream URI
            stream_setup = {
                'Stream': 'RTP-Unicast',
                'Transport': {'Protocol': 'RTSP'}
            }
            
            uri_response = media_service.GetStreamUri({
                'StreamSetup': stream_setup,
                'ProfileToken': profile.token
            })
            
            return uri_response.Uri
            
        except Exception as e:
            print(f"Error getting RTSP URL: {e}")
            return None
    
    @staticmethod
    def get_snapshot_url(camera: ONVIFCamera, profile_index: int = 0) -> Optional[str]:
        """Get snapshot/thumbnail URL from camera"""
        try:
            media_service = camera.create_media_service()
            profiles = media_service.GetProfiles()
            
            if not profiles:
                return None
            
            profile = profiles[profile_index] if profile_index < len(profiles) else profiles[0]
            
            snapshot_uri = media_service.GetSnapshotUri({'ProfileToken': profile.token})
            
            return snapshot_uri.Uri
            
        except Exception as e:
            print(f"Error getting snapshot URL: {e}")
            return None
    
    @staticmethod
    def test_rtsp_stream(rtsp_url: str, timeout: int = 5) -> bool:
        """
        Test if RTSP stream is accessible
        
        Args:
            rtsp_url: RTSP URL to test
            timeout: Timeout in seconds
            
        Returns:
            True if stream is accessible, False otherwise
        """
        try:
            import cv2
            
            cap = cv2.VideoCapture(rtsp_url)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Try to read one frame
            ret, frame = cap.read()
            cap.release()
            
            return ret
            
        except Exception as e:
            print(f"Error testing RTSP stream: {e}")
            return False
    
    @staticmethod
    def get_capabilities(camera: ONVIFCamera) -> Dict:
        """Get camera capabilities (PTZ, analytics, etc.)"""
        try:
            capabilities = camera.devicemgmt.GetCapabilities()
            
            return {
                "ptz": hasattr(capabilities, 'PTZ') and capabilities.PTZ is not None,
                "imaging": hasattr(capabilities, 'Imaging') and capabilities.Imaging is not None,
                "analytics": hasattr(capabilities, 'Analytics') and capabilities.Analytics is not None,
                "events": hasattr(capabilities, 'Events') and capabilities.Events is not None,
                "media": hasattr(capabilities, 'Media') and capabilities.Media is not None
            }
            
        except Exception as e:
            print(f"Error getting capabilities: {e}")
            return {}


# Helper functions for quick access
def discover_onvif_cameras(timeout: int = 5) -> List[Dict]:
    """Quick function to discover cameras"""
    return ONVIFCameraManager.discover_cameras(timeout)

def add_onvif_camera(ip: str, port: int, username: str, password: str) -> Dict:
    """
    Add and verify ONVIF camera
    
    Returns:
        Dictionary with camera info and stream URLs
    """
    # Connect to camera
    camera = ONVIFCameraManager.connect_camera(ip, port, username, password)
    
    if not camera:
        raise Exception("Failed to connect to camera. Check IP, port, and credentials.")
    
    # Get camera information
    camera_info = ONVIFCameraManager.get_camera_info(camera)
    
    # Get RTSP URLs
    rtsp_url_main = ONVIFCameraManager.get_rtsp_url(camera, 0)
    rtsp_url_sub = ONVIFCameraManager.get_rtsp_url(camera, 1)
    
    # Get snapshot URL
    snapshot_url = ONVIFCameraManager.get_snapshot_url(camera)
    
    # Get capabilities
    capabilities = ONVIFCameraManager.get_capabilities(camera)
    
    return {
        "ip": ip,
        "port": port,
        "manufacturer": camera_info.get("manufacturer", "Unknown"),
        "model": camera_info.get("model", "Unknown"),
        "firmware_version": camera_info.get("firmware_version", ""),
        "serial_number": camera_info.get("serial_number", ""),
        "rtsp_url_main": rtsp_url_main,
        "rtsp_url_sub": rtsp_url_sub,
        "snapshot_url": snapshot_url,
        "capabilities": capabilities,
        "full_info": camera_info
    }
