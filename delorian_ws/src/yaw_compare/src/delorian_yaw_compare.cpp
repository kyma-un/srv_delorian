#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"
#include <memory>
#include <rclcpp/logging.hpp>
#include <rclcpp/node.hpp>
#include <rclcpp/subscription.hpp>
#include <rclcpp/utilities.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <type_traits>

using namespace std::chrono_literals;

class yawCompare : public rclcpp::Node {
public:

  yawCompare() : Node("yaw_compare_node") {
    auto wheels_odometry_callback = [this](nav_msgs::msg::Odometry::UniquePtr msg) -> void {
      RCLCPP_INFO(this->get_logger(), "Escuche odometría de ruedas: '%f'", msg->pose.pose.orientation.z);
    };
    auto real_odometry_callback=[this](nav_msgs::msg::Odometry::UniquePtr msg) -> void {
      RCLCPP_INFO(this->get_logger(), "Escuche odometría real: '%f'", msg->pose.pose.orientation.z);
    };
    subscription_wheel = this->create_subscription<nav_msgs::msg::Odometry>(
        "/odometry/wheel", 10, wheels_odometry_callback);
    subscription_ground=this->create_subscription<nav_msgs::msg::Odometry>(
        "/odometry/ground_truth", 10, real_odometry_callback);
      };

private:
  rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr subscription_wheel;
  rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr subscription_ground;
};

int main(int argc, char *argv[]) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<yawCompare>());
  rclcpp::shutdown();
  return 0;
}
