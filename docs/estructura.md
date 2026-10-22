# Estructura del Delorian (ROS 2)

Workspace: `delorian_ws/`. Distribución: ROS 2 Jazzy. Simulador: gz sim (Harmonic).

## Paquetes

```
delorian_ws/src/
├── delorian_description/       descripción del robot (vale para real y simulación)
│   ├── urdf/
│   │   ├── delorian.urdf.xacro   PRINCIPAL: incluye los otros; argumento sim:=true/false
│   │   ├── delorian_core.xacro   robot físico: links, joints, inercias, colores
│   │   └── delorian.gazebo.xacro solo simulación: fricción, DiffDrive, joint_states, cámara
│   ├── meshes/
│   │   ├── main_frame.stl        malla del chasis (4 MB)
│   │   └── wheel.stl             malla de la rueda (2 MB)
│   ├── rviz/display.rviz         configuración de RViz
│   └── launch/display.launch.py  solo RViz + joint_state_publisher_gui (sin física)
│
├── delorian_gz/                simulación en Gazebo
│   ├── worlds/delorian.sdf       mundo: suelo, sol, sistema Sensors y cajas de prueba
│   ├── config/bridge.yaml        puente gz <-> ROS 2 (ros_gz_bridge)
│   └── launch/sim.launch.py      gz sim + rsp + spawn + bridge + RViz
│
├── delorian_bringup/           (vacío) lanzamiento del robot real
├── delorian_control/           (vacío) cinemática inversa, interfaz con el STM32
├── delorian_interfaces/        (vacío) mensajes y servicios propios
└── delorian_navigation/        (vacío) Nav2 y rtabmap
```

## Árbol de frames (TF)

```
odom                      ← DiffDrive en Gazebo; el EKF en el robot real
 └── base_footprint       proyección del robot en el suelo
      └── base_link       centro de las 4 ruedas, a la altura del eje (+X = frente)
           ├── chassis              chasis con los números del CAD (masa, colisión, malla)
           ├── front_left_wheel     ( 0.263,  0.24)
           ├── rear_left_wheel      (-0.263,  0.24)
           ├── front_right_wheel    ( 0.263, -0.24)
           ├── rear_right_wheel     (-0.263, -0.24)
           └── oak_link             cámara OAK-D S2 (0.335, 0, 0.30)
                └── oak_optical_link   ejes ópticos (z adelante, x derecha, y abajo)
```

Medidas: radio de rueda 0.128 m, ancho 0.168 m, distancia entre ejes 0.526 m, trocha 0.480 m.

## Tópicos en simulación

| Tópico ROS 2 | Tipo | Origen |
|---|---|---|
| `/cmd_vel` | `geometry_msgs/Twist` | entrada al DiffDrive |
| `/odometry/wheel` | `nav_msgs/Odometry` | DiffDrive (no se usa `/odom`: ese nombre es de `rgbd_odometry`) |
| `/joint_states` | `sensor_msgs/JointState` | JointStatePublisher de gz |
| `/tf` | `tf2_msgs/TFMessage` | odom → base_footprint del DiffDrive |
| `/oak/rgb/image_raw` | `sensor_msgs/Image` | cámara simulada |
| `/oak/depth/image_raw` | `sensor_msgs/Image` (32FC1) | cámara simulada |
| `/oak/rgb/camera_info` | `sensor_msgs/CameraInfo` | cámara simulada |
| `/oak/depth/points` | `sensor_msgs/PointCloud2` | cámara simulada |

Los nombres `/oak/*` son los mismos que publica `depthai-ros` en el robot real, para que el
resto del stack (rtabmap, Nav2) no cambie entre simulación y hardware.

## Cómo compilar y lanzar

El desarrollo se hace dentro de la distrobox `ros2-iso` (Jazzy, home aislado):

```sh
distrobox enter ros2-iso
cd /home/jysusman/Kyma/srv_delorian/delorian_ws
colcon build --symlink-install
source install/setup.zsh
```

Solo el modelo en RViz, con sliders para mover las ruedas:

```sh
ros2 launch delorian_description display.launch.py
```

Simulación completa (Gazebo + RViz):

```sh
ros2 launch delorian_gz sim.launch.py
ros2 launch delorian_gz sim.launch.py rviz:=false
ros2 launch delorian_gz sim.launch.py world:=empty.sdf
```

Teleoperar el robot:

```sh
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

## Notas

- El mundo propio `delorian.sdf` existe porque el `empty.sdf` que trae gz **no** carga el
  sistema `Sensors`, sin el cual las cámaras no renderizan.
- Las STL exportadas desde el CAD traen en la cabecera la marca `COLOR=`/`MATERIAL=`, que hace
  que RViz ignore el `<material>` del URDF y pinte todo de rojo. Hay que borrar esa cabecera
  cada vez que se reexporten:

  ```sh
  for f in main_frame.stl wheel.stl; do printf '%-80s' "delorian $f" | dd of="$f" bs=1 count=80 conv=notrunc; done
  ```
- Al convertir el URDF a SDF, gz fusiona los links sin inercia unidos por joints fijos, así que
  el sensor aparece colgado de `base_footprint`. Es normal: la pose y el `frame_id` se conservan.
