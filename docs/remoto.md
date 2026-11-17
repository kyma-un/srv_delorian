# Trabajar entre dos equipos

Para correr la simulación en un equipo (el que tiene mejor GPU) y mirarla o usar sus
tópicos desde otro, en la red local o por VPN ([Tailscale](https://tailscale.com/)).
Requiere tener el entorno de [entorno.md](entorno.md) en los dos.

## ROS 2 entre equipos

ROS 2 se descubre por multicast UDP, así que dos cosas pueden aislar las máquinas:

**Firewall.** Si el equipo tiene `ufw` activo, bloquea el tráfico de DDS. En los dos
equipos, permitir UDP desde la red local y desde la VPN:

```sh
sudo ufw allow from 192.168.2.0/24 proto udp comment 'ROS 2 DDS'   # cambiar por tu subred
sudo ufw allow in on tailscale0 proto udp comment 'ROS 2 por Tailscale'
```

**Multicast que no llega.** Tailscale no transporta multicast, y algunos routers tampoco
lo pasan entre WiFi y cable (un equipo por cable y el otro por WiFi en la misma casa). En
esos casos los nodos no se encuentran solos. Desde Jazzy basta con darle a cada máquina
la IP de la otra, dentro del contenedor:

```sh
export ROS_STATIC_PEERS="<IP del otro equipo>"   # de Tailscale o de la red local; varias con ';'
```

Donde el multicast sí funciona no estorba. Las dos máquinas deben tener el mismo
`ROS_DOMAIN_ID` (o ninguno).

Comprobación: en un equipo `ros2 run demo_nodes_cpp talker`, en el otro
`ros2 topic echo /chatter`.

### Qué pasa bien por la red y qué no

TF, odometría, IMU, GPS y `/clock` son mensajes pequeños y llegan sin problema. La imagen
y sobre todo la nube de puntos de la cámara **no**: `/oak/depth/points` son unos 9 MB/s,
DDS la parte en muchos fragmentos UDP y por WiFi basta perder uno para descartar el
mensaje entero; como es `RELIABLE`, además reintenta y atasca el resto. Para ver la
cámara, abrir RViz en el equipo que simula (y verlo con escritorio remoto), o mandar la
imagen comprimida.

## Gazebo remoto

La simulación (física y sensores) corre en un equipo y la ventana de Gazebo se abre en
otro, que solo dibuja la escena. gz-transport tiene sus propias reglas, aparte de las de ROS:

- Descubre por multicast UDP (puertos 10317/10318), pero manda los datos por **TCP** en
  puertos aleatorios: en `ufw` hay que permitir también TCP.

  ```sh
  sudo ufw allow from 192.168.2.0/24 proto tcp comment 'gz-transport'
  sudo ufw allow in on tailscale0 proto tcp comment 'gz-transport por Tailscale'
  ```
- `GZ_IP`: la IP por la que se anuncia cada equipo. `sim.launch.py` usa `127.0.0.1` por
  defecto (ver "Si Gazebo abre en negro" en [entorno.md](entorno.md)); para verlo desde
  fuera se le pasa `gz_ip:=<IP>`.
- `GZ_PARTITION`: si no se define, cada equipo usa `hostname:usuario` y se ignoran entre
  sí. `sim.launch.py` pone `delorian`; el otro equipo debe usar la misma.
- `GZ_RELAY`: la IP del otro equipo, necesaria cuando no hay multicast (VPN). En **los
  dos** sentidos.

En el equipo que simula (`gui:=false` corre solo el servidor; la cámara sigue
renderizando con la GPU):

```sh
ros2 launch delorian_gz sim.launch.py gz_ip:=<IP propia> gz_relay:=<IP del otro> gui:=false rviz:=false
```

En el que mira:

```sh
GZ_PARTITION=delorian GZ_IP=<IP propia> GZ_RELAY=<IP del que simula> gz sim -g
```

**Mallas que no cargan.** El servidor manda las rutas de las mallas ya resueltas, con el
home de su máquina (`/home/<usuario>/.gz/fuel/...`, `/home/<usuario>/srv_delorian/...`).
Si en el que mira no existen, los árboles y conos (y el robot) no aparecen. Lo más simple
es crear esas rutas con enlaces dentro del contenedor:

```sh
sudo mkdir -p /home/<usuario remoto>
sudo ln -sfn ~/.gz /home/<usuario remoto>/.gz
sudo ln -sfn <ruta de tu clon> /home/<usuario remoto>/srv_delorian
```

Los modelos de Fuel tienen que estar descargados también en el que mira (basta con haber
lanzado `sim.launch.py` una vez).
