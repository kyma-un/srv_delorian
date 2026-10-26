# Entorno de desarrollo

ROS 2 Jazzy solo se distribuye para Ubuntu 24.04. En Ubuntu se instala siguiendo la
[guía oficial](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html) y
basta con seguir [estructura.md](estructura.md).

En cualquier otra distribución (Arch, CachyOS, Fedora, openSUSE) la opción más limpia es
un contenedor con [distrobox](https://distrobox.it/), que comparte el usuario, el
servidor gráfico y los dispositivos con el anfitrión. Así `gz sim` y `rviz2` abren
ventanas normales y se puede editar el repositorio desde el editor del anfitrión.

## Crear el contenedor

```sh
distrobox create --name ros2-iso \
  --image docker.io/osrf/ros:jazzy-desktop-full \
  --home ~/distrobox/ros2-home \
  --nvidia
distrobox enter ros2-iso
```

- `--home` le da al contenedor un directorio personal propio, para que sus
  configuraciones (`.bashrc`, `.ros`, `.gazebo`) no se mezclen con las del anfitrión.
  El anfitrión sigue montado, así que el repositorio se ve en su ruta de siempre.
- `--nvidia` monta las bibliotecas de NVIDIA del anfitrión. En equipos híbridos sin MUX,
  omitirlo hace que Gazebo renderice con la gráfica integrada: funciona, pero más lento.
  No se puede agregar después; hay que recrear el contenedor.

## Dentro del contenedor

Una sola vez:

```sh
sudo rosdep init
rosdep update
echo 'source /opt/ros/jazzy/setup.bash' >> ~/.bashrc
```

Después se sigue con [estructura.md](estructura.md): `rosdep install` instala las
dependencias de los paquetes (`ros_gz`, `rtabmap_ros`, `xacro`, ...) y `colcon build`
compila el workspace.

## Uso diario

```sh
distrobox enter ros2-iso   # entrar
exit                       # salir
podman start ros2-iso      # tras reiniciar el equipo, si no arranca solo
```

## Notas

- La primera vez que se lanza `sim.launch.py` hace falta conexión a internet: el mundo
  `delorian.sdf` incluye modelos de [Gazebo Fuel](https://app.gazebosim.org/fuel) (árboles
  y conos) que se descargan a `~/.gz/fuel` y tardan un rato.
- Para el robot real, en la Raspberry Pi, `delorian_gz` no se necesita:
  `colcon build --packages-skip delorian_gz`.

## Si Gazebo abre en negro y el robot no aparece

Síntoma: la ventana de Gazebo abre pero la escena está negra, el robot nunca se inserta
y en la consola `create` repite cada 5 segundos:

```
[create-3] [INFO] [ros_gz_sim]: Requesting list of world names.
```

Causa: Gazebo son dos procesos (servidor y interfaz) que se descubren entre sí por
multicast UDP. `gz-transport` se anuncia por la primera interfaz de red que no sea `lo`,
y las tarjetas WiFi no devuelven a la propia máquina el multicast que ellas mismas
envían, así que los dos procesos quedan sordos entre sí. En un equipo con otra interfaz
disponible (por ejemplo la de Tailscale) el problema no aparece, lo que lo hace confuso:
el mismo contenedor funciona en una máquina y falla en otra.

Solución: anunciarse por loopback, que es donde corre todo.

```sh
export GZ_IP=127.0.0.1
```

`sim.launch.py` ya lo hace por su cuenta, así que esto solo hace falta al llamar a `gz`
a mano (`gz sim -s`, `gz sim -g`, `gz model --list`, ...). Comprobación rápida, con el
servidor corriendo: `gz model --list` debe listar los modelos del mundo en vez de dar
`Service call to [/gazebo/worlds] timed out`.
