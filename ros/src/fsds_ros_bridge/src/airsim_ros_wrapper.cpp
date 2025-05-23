#include <airsim_ros_wrapper.h>
#include <boost/make_shared.hpp>
// #include <pluginlib/class_list_macros.h>
// PLUGINLIB_EXPORT_CLASS(AirsimROSWrapper, nodelet::Nodelet)
#include "common/AirSimSettings.hpp"

AirsimROSWrapper::AirsimROSWrapper(const ros::NodeHandle& nh, const ros::NodeHandle& nh_private, const std::string& host_ip, double timeout_sec) : nh_(nh),
                                                                                                                               nh_private_(nh_private),
                                                                                                                               lidar_async_spinner_(1, &lidar_timer_cb_queue_), // same as above, but for lidar
                                                                                                                               airsim_client_(host_ip, RpcLibPort, timeout_sec),
                                                                                                                               airsim_client_lidar_(host_ip, RpcLibPort, timeout_sec)
{
    initialize_airsim(timeout_sec);
    try {
        std::string settings_text = airsim_client_.getSettingsString();

        msr::airlib::AirSimSettings::initializeSettings(settings_text);
        msr::airlib::AirSimSettings::singleton().load();
        for (const auto &warning : msr::airlib::AirSimSettings::singleton().warning_messages)
        {
            ROS_WARN_STREAM("Configuration warning: " << warning);
        }
        for (const auto &error : msr::airlib::AirSimSettings::singleton().error_messages)
        {
            ROS_ERROR_STREAM("Configuration error: " << error);
        }
    }
    catch (std::exception &ex) {
        throw std::invalid_argument(std::string("Failed loading settings.json.") + ex.what());
    }
    
    initialize_ros();
    initialize_statistics();

    ROS_INFO_STREAM("AirsimROSWrapper Initialized!");
}

void AirsimROSWrapper::initialize_airsim(double timeout)
{
    // todo do not reset if already in air?
    try
    {
        double elapsed = 0.0;
        ROS_INFO_STREAM("Waiting for connection - ");
        airsim_client_.confirmConnection(timeout);
        airsim_client_lidar_.confirmConnection(timeout);
        ROS_INFO_STREAM("Connected to the simulator!");
    }
    catch (rpc::rpc_error& e)
    {
        std::string msg = e.get_error().as<std::string>();
        ROS_ERROR_STREAM("Exception raised by the API, something went wrong." << std::endl << msg);
    }
}

void AirsimROSWrapper::initialize_statistics()
{
    setCarControlsStatistics = ros_bridge::Statistics("setCarControls");
    
    if(enabled_sensors.gps){
        getGpsDataStatistics = ros_bridge::Statistics("getGpsData");
        global_gps_pub_statistics = ros_bridge::Statistics("global_gps_pub");
    }
    
    getCarStateStatistics = ros_bridge::Statistics("getCarState");
    
    if(enabled_sensors.imu){
        getImuStatistics = ros_bridge::Statistics("getImu");
        imu_pub_statistics = ros_bridge::Statistics("imu_pub");
    }

    if(enabled_sensors.gss){
        getGSSStatistics = ros_bridge::Statistics("getGSS");
        gss_pub_statistics = ros_bridge::Statistics("gss_pub");
    }
    
    control_cmd_sub_statistics = ros_bridge::Statistics("control_cmd_sub");
    odom_pub_statistics = ros_bridge::Statistics("odom_pub");

    // Populate statistics obj vector
    // statistics_obj_ptr = {&setCarControlsStatistics, &getGpsDataStatistics, &getCarStateStatistics, &control_cmd_sub_statistics, &global_gps_pub_statistics, &odom_local_ned_pub_statistics};
}

void AirsimROSWrapper::publish_track() {
    CarApiBase::RefereeState state;
    try{
        std::unique_lock<std::recursive_mutex> lck(car_control_mutex_);
        state = airsim_client_.getRefereeState();
        lck.unlock();
    } catch (rpc::rpc_error& e)
    {
        std::string msg = e.get_error().as<std::string>();
        ROS_ERROR_STREAM("Exception raised by the API, something went wrong while retreiving referee state for publishing track." << std::endl << msg);
    }
    
    // Get car initial position
    car_start_pos = state.car_start_location;

    fs_msgs::Track track;
    for (const auto& cone : state.cones) {
        fs_msgs::Cone cone_object;
        // 0.01 is a scaling constant that converts to meters
        cone_object.location.x = cone.location.x != 0 ? (cone.location.x - car_start_pos.x)*0.01 : 0;
        // Negative sign follows ENU convention
        cone_object.location.y = cone.location.y != 0 ? -(cone.location.y - car_start_pos.y)*0.01 : 0;
        if (cone.color == CarApiBase::ConeColor::Yellow) {
            cone_object.color = fs_msgs::Cone::YELLOW;
        } else if (cone.color == CarApiBase::ConeColor::Blue) {
            cone_object.color = fs_msgs::Cone::BLUE;
        } else if (cone.color == CarApiBase::ConeColor::OrangeLarge) {
            cone_object.color = fs_msgs::Cone::ORANGE_BIG;
        } else if (cone.color == CarApiBase::ConeColor::OrangeSmall) {
            cone_object.color = fs_msgs::Cone::ORANGE_SMALL;
        } else if (cone.color == CarApiBase::ConeColor::Unknown) {
            cone_object.color = fs_msgs::Cone::UNKNOWN;
        }
        track.track.push_back(cone_object);

    }

    track_pub.publish(track);
}

void AirsimROSWrapper::initialize_ros()
{

    // ros params
    double update_odom_every_n_sec;
    double update_gps_every_n_sec;
    double update_imu_every_n_sec;
    double update_gss_every_n_sec;
    double publish_static_tf_every_n_sec;
    bool manual_mode;
    nh_private_.getParam("mission_name", mission_name_);
    nh_private_.getParam("track_name", track_name_);
    nh_private_.getParam("competition_mode", competition_mode_);
    nh_private_.getParam("manual_mode", manual_mode);
    nh_private_.getParam("update_odom_every_n_sec", update_odom_every_n_sec);
    nh_private_.getParam("update_gps_every_n_sec", update_gps_every_n_sec);
    nh_private_.getParam("update_imu_every_n_sec", update_imu_every_n_sec);
    nh_private_.getParam("update_gss_every_n_sec", update_gss_every_n_sec);
    nh_private_.getParam("publish_static_tf_every_n_sec", publish_static_tf_every_n_sec);

    create_ros_pubs_from_settings_json();

    if(!competition_mode_) {
        odom_update_timer_ = nh_private_.createTimer(ros::Duration(update_odom_every_n_sec), &AirsimROSWrapper::odom_cb, this);
		extra_info_timer_ = nh_private_.createTimer(ros::Duration(1), &AirsimROSWrapper::extra_info_cb, this);
    }
    
    if(enabled_sensors.gps)
        gps_update_timer_ = nh_private_.createTimer(ros::Duration(update_gps_every_n_sec), &AirsimROSWrapper::gps_timer_cb, this);
    
    if(enabled_sensors.imu)
        imu_update_timer_ = nh_private_.createTimer(ros::Duration(update_imu_every_n_sec), &AirsimROSWrapper::imu_timer_cb, this);
    
    if(enabled_sensors.gss)
        gss_update_timer_ = nh_private_.createTimer(ros::Duration(update_gss_every_n_sec), &AirsimROSWrapper::gss_timer_cb, this);

    statictf_timer_ = nh_private_.createTimer(ros::Duration(publish_static_tf_every_n_sec), &AirsimROSWrapper::statictf_cb, this);

    statistics_timer_ = nh_private_.createTimer(ros::Duration(1), &AirsimROSWrapper::statistics_timer_cb, this);
    go_signal_timer_ = nh_private_.createTimer(ros::Duration(1), &AirsimROSWrapper::go_signal_timer_cb, this);
    go_timestamp_ = ros::Time::now();

    airsim_client_.enableApiControl(!manual_mode, vehicle_name);

    if(!competition_mode_) {
        publish_track();
    }
}

// XmlRpc::XmlRpcValue can't be const in this case
void AirsimROSWrapper::create_ros_pubs_from_settings_json()
{
    go_signal_pub_ = nh_.advertise<fs_msgs::GoSignal>("signal/go", 1);
    finished_signal_sub_ = nh_.subscribe("signal/finished", 1, &AirsimROSWrapper::finished_signal_cb, this);

    static_tf_msg_vec_.clear();
    lidar_pub_vec_.clear();
    // vehicle_imu_map_;
    // callback_queues_.clear();


    // iterate over std::map<std::string, std::unique_ptr<VehicleSetting>> vehicles;
    for (const auto& curr_vehicle_elem : msr::airlib::AirSimSettings::singleton().vehicles)
    {
        auto& vehicle_setting = curr_vehicle_elem.second;
        auto curr_vehicle_name = curr_vehicle_elem.first;

        if(curr_vehicle_name != "FSCar") {
            throw std::invalid_argument("Only the FSCar vehicle_name is allowed.");
        }

        set_nans_to_zeros_in_pose(*vehicle_setting);

        enabled_sensors.gss = (vehicle_setting->sensors.find("GSS") != vehicle_setting->sensors.end());
        enabled_sensors.gps = (vehicle_setting->sensors.find("Gps") != vehicle_setting->sensors.end());
        enabled_sensors.imu = (vehicle_setting->sensors.find("Imu") != vehicle_setting->sensors.end());

        enabled_sensors.print();

        vehicle_name = curr_vehicle_name;

        if(enabled_sensors.gps)
            global_gps_pub = nh_.advertise<sensor_msgs::NavSatFix>("gps", 10);
            
        if(enabled_sensors.imu)
            imu_pub = nh_.advertise<sensor_msgs::Imu>("imu", 10);
        
        if(enabled_sensors.gss)
            gss_pub = nh_.advertise<geometry_msgs::TwistWithCovarianceStamped>("gss", 10);

        bool UDP_control;
        nh_private_.getParam("UDP_control", UDP_control);

        if(UDP_control){
            control_cmd_sub = nh_.subscribe<fs_msgs::ControlCommand>("control_command", 1, boost::bind(&AirsimROSWrapper::car_control_cb, this, _1, vehicle_name), NULL, ros::TransportHints().udp());
        } else {
            control_cmd_sub = nh_.subscribe<fs_msgs::ControlCommand>("control_command", 1, boost::bind(&AirsimROSWrapper::car_control_cb, this, _1, vehicle_name));
        }

        if(!competition_mode_) {
            odom_pub = nh_.advertise<nav_msgs::Odometry>("testing_only/odom", 10);
            track_pub = nh_.advertise<fs_msgs::Track>("testing_only/track", 10, true);
			extra_info_pub = nh_.advertise<fs_msgs::ExtraInfo>("testing_only/extra_info", 10, true);
        }
        
        // iterate over camera map std::map<std::string, CameraSetting> cameras;
        for (auto& curr_camera_elem : vehicle_setting->cameras)
        {
            auto& camera_setting = curr_camera_elem.second;
            auto& curr_camera_name = curr_camera_elem.first;
            set_nans_to_zeros_in_pose(*vehicle_setting, camera_setting);
            append_static_camera_tf(curr_vehicle_name, curr_camera_name, camera_setting);
            
        }

        // iterate over sensors std::map<std::string, std::unique_ptr<SensorSetting>> sensors;
        for (auto& curr_sensor_map : vehicle_setting->sensors)
        {
            auto& sensor_name = curr_sensor_map.first;
            auto& sensor_setting = curr_sensor_map.second;

            switch (sensor_setting->sensor_type)
            {
            case msr::airlib::SensorBase::SensorType::Imu:
            {              
                break;
            }
            case msr::airlib::SensorBase::SensorType::Gps:
            {
                break;
            }
            case msr::airlib::SensorBase::SensorType::Distance:
            {
                break;
            }
            case msr::airlib::SensorBase::SensorType::GSS:
            {
                break;
            }
            case msr::airlib::SensorBase::SensorType::Lidar:
            {
                std::cout << "Lidar" << std::endl;
                auto lidar_setting = *static_cast<LidarSetting *>(sensor_setting.get());
                set_nans_to_zeros_in_pose(*vehicle_setting, lidar_setting);
                append_static_lidar_tf(curr_vehicle_name, sensor_name, lidar_setting); // todo is there a more readable way to down-cast?
                lidar_names_vec_.push_back(sensor_name);
                lidar_pub_vec_.push_back(nh_.advertise<sensor_msgs::PointCloud2>("lidar/" + sensor_name, 10));
                lidar_pub_vec_statistics.push_back(ros_bridge::Statistics(sensor_name + "_Publisher"));
                getLidarDataVecStatistics.push_back(ros_bridge::Statistics(sensor_name + "_RpcCaller"));

                auto lidar_index = lidar_pub_vec_.size() -1;

                auto x = [this, sensor_name, lidar_index](const ros::TimerEvent& te) { this->lidar_timer_cb(te, sensor_name, lidar_index); };
                ros::TimerOptions timer_options(ros::Duration(float(1) / float(lidar_setting.horizontal_rotation_frequency)), x, &lidar_timer_cb_queue_);
                airsim_lidar_update_timers_.push_back(nh_private_.createTimer(timer_options));
                break;
            }
            default:
            {
                throw std::invalid_argument("Unexpected sensor type (D) with name " + sensor_setting->sensor_name);
            }
            }
        }
    }

    reset_srvr_ = nh_.advertiseService("reset", &AirsimROSWrapper::reset_srv_cb, this);
}

ros::Time AirsimROSWrapper::make_ts(uint64_t unreal_ts)
{
   // unreal timestamp is a unix nanosecond timestamp just like ros.
   // We can do direct translation as long as ros is not running in simulated time mode.
   ros::Time out;
   return out.fromNSec(unreal_ts);
}

// todo add reset by vehicle_name API to airlib
// todo not async remove waitonlasttask
bool AirsimROSWrapper::reset_srv_cb(fs_msgs::Reset::Request& request, fs_msgs::Reset::Response& response)
{
    std::lock_guard<std::recursive_mutex> guard(car_control_mutex_);

    airsim_client_.reset();
    return true; //todo
}

tf2::Quaternion AirsimROSWrapper::get_tf2_quat(const msr::airlib::Quaternionr& airlib_quat) const
{
    return tf2::Quaternion(airlib_quat.x(), airlib_quat.y(), airlib_quat.z(), airlib_quat.w());
}

msr::airlib::Quaternionr AirsimROSWrapper::get_airlib_quat(const geometry_msgs::Quaternion& geometry_msgs_quat) const
{
    return msr::airlib::Quaternionr(geometry_msgs_quat.w, geometry_msgs_quat.x, geometry_msgs_quat.y, geometry_msgs_quat.z);
}

msr::airlib::Quaternionr AirsimROSWrapper::get_airlib_quat(const tf2::Quaternion& tf2_quat) const
{
    return msr::airlib::Quaternionr(tf2_quat.w(), tf2_quat.x(), tf2_quat.y(), tf2_quat.z());
}

nav_msgs::Odometry AirsimROSWrapper::get_odom_msg_from_airsim_state(const msr::airlib::CarApiBase::CarState& car_state) const
{
    nav_msgs::Odometry odom_enu_msg;
    odom_enu_msg.header.frame_id = "fsds/map";
    odom_enu_msg.header.stamp = ros::Time::now();
    odom_enu_msg.child_frame_id = "fsds/FSCar";
    odom_enu_msg.pose.pose.position.x = car_state.getPosition().x();
    odom_enu_msg.pose.pose.position.y = car_state.getPosition().y();
    odom_enu_msg.pose.pose.position.z = car_state.getPosition().z();

    odom_enu_msg.pose.pose.orientation.x = car_state.getOrientation().x();
    odom_enu_msg.pose.pose.orientation.y = car_state.getOrientation().y();
    odom_enu_msg.pose.pose.orientation.z = car_state.getOrientation().z();
    odom_enu_msg.pose.pose.orientation.w = car_state.getOrientation().w();

    odom_enu_msg.twist.twist.linear.x = car_state.kinematics_estimated.twist.linear.x();
    odom_enu_msg.twist.twist.linear.y = car_state.kinematics_estimated.twist.linear.y();
    odom_enu_msg.twist.twist.linear.z = car_state.kinematics_estimated.twist.linear.z();
    odom_enu_msg.twist.twist.angular.x = car_state.kinematics_estimated.twist.angular.x();
    odom_enu_msg.twist.twist.angular.y = car_state.kinematics_estimated.twist.angular.y();
    odom_enu_msg.twist.twist.angular.z = car_state.kinematics_estimated.twist.angular.z();

    return odom_enu_msg;
}


// https://docs.ros.org/jade/api/sensor_msgs/html/point__cloud__conversion_8h_source.html#l00066
// look at UnrealLidarSensor.cpp UnrealLidarSensor::getPointCloud() for math
// read this carefully https://docs.ros.org/kinetic/api/sensor_msgs/html/msg/PointCloud2.html
sensor_msgs::PointCloud2 AirsimROSWrapper::get_lidar_msg_from_airsim(const std::string &lidar_name, const msr::airlib::LidarData& lidar_data) const
{
    sensor_msgs::PointCloud2 lidar_msg;
    lidar_msg.header.frame_id = "fsds/"+lidar_name;

    if (lidar_data.point_cloud.size() > 3)
    {
        lidar_msg.height = 1;
        lidar_msg.width = lidar_data.point_cloud.size() / 3;

        lidar_msg.fields.resize(3);
        lidar_msg.fields[0].name = "x";
        lidar_msg.fields[1].name = "y";
        lidar_msg.fields[2].name = "z";
        int offset = 0;

        for (size_t d = 0; d < lidar_msg.fields.size(); ++d, offset += 4)
        {
            lidar_msg.fields[d].offset = offset;
            lidar_msg.fields[d].datatype = sensor_msgs::PointField::FLOAT32;
            lidar_msg.fields[d].count = 1;
        }

        lidar_msg.is_bigendian = false;
        lidar_msg.point_step = offset; // 4 * num fields
        lidar_msg.row_step = lidar_msg.point_step * lidar_msg.width;

        lidar_msg.is_dense = true; // todo
        std::vector<float> data_std = lidar_data.point_cloud;

        const unsigned char *bytes = reinterpret_cast<const unsigned char *>(&data_std[0]);
        std::vector<unsigned char> lidar_msg_data(bytes, bytes + sizeof(float) * data_std.size());
        lidar_msg.data = std::move(lidar_msg_data);
    }
    return lidar_msg;
}

// todo covariances
sensor_msgs::Imu AirsimROSWrapper::get_imu_msg_from_airsim(const msr::airlib::ImuBase::Output& imu_data)
{
    sensor_msgs::Imu imu_msg;

    imu_msg.orientation.x = imu_data.orientation.x();
    imu_msg.orientation.y = imu_data.orientation.y();
    imu_msg.orientation.z = imu_data.orientation.z();
    imu_msg.orientation.w = imu_data.orientation.w();

    // Publish IMU ang rates in radians per second
    imu_msg.angular_velocity.x = imu_data.angular_velocity.x();
    imu_msg.angular_velocity.y = imu_data.angular_velocity.y();
    imu_msg.angular_velocity.z = imu_data.angular_velocity.z();

    // meters/s2^m
    imu_msg.linear_acceleration.x = imu_data.linear_acceleration.x();
    imu_msg.linear_acceleration.y = imu_data.linear_acceleration.y();
    imu_msg.linear_acceleration.z = imu_data.linear_acceleration.z();

    imu_msg.header.stamp = make_ts(imu_data.time_stamp);

    return imu_msg;
}


sensor_msgs::NavSatFix AirsimROSWrapper::get_gps_sensor_msg_from_airsim_geo_point(const msr::airlib::GeoPoint& geo_point) const
{
    sensor_msgs::NavSatFix gps_msg;
    gps_msg.header.frame_id = "fsds/" + vehicle_name;
    gps_msg.latitude = geo_point.latitude;
    gps_msg.longitude = geo_point.longitude;
    gps_msg.altitude = geo_point.altitude;
    return gps_msg;
}

void AirsimROSWrapper::car_control_cb(const fs_msgs::ControlCommand::ConstPtr& msg, const std::string& vehicle_name)
{
    ros_bridge::ROSMsgCounter counter(&control_cmd_sub_statistics);

    // Only allow positive braking and throttle commands to be passed through
    CarApiBase::CarControls controls;
    controls.throttle = msg->throttle < 0.0 ? 0.0 : msg->throttle;
    controls.steering = msg->steering;
    controls.brake = msg->brake < 0.0 ? 0.0 : msg->brake;
    ros::Time time = msg->header.stamp;

    {
        ros_bridge::Timer timer(&setCarControlsStatistics);
        std::unique_lock<std::recursive_mutex> lck(car_control_mutex_);
        airsim_client_.setCarControls(controls, vehicle_name);
        lck.unlock();
    }
}

void AirsimROSWrapper::odom_cb(const ros::TimerEvent& event)
{
    try
    {
        msr::airlib::CarApiBase::CarState state;
        {
            ros_bridge::Timer timer(&getCarStateStatistics);
            std::unique_lock<std::recursive_mutex> lck(car_control_mutex_);
            state = airsim_client_.getCarState(vehicle_name);
            lck.unlock();
        }

        nav_msgs::Odometry message_enu = this->get_odom_msg_from_airsim_state(state);

        // the wrapper requests vehicle position faster then unreal simulates.
        // We shouldn't be sending duplicate messages as explained in #156
        // So we only publish a message if it changes, making an exception for when vehicle is not moving.
        if(AirsimROSWrapper::equalsMessage(message_enu, message_enu_previous_) && !(message_enu.twist.twist.linear.x == 0 && message_enu.twist.twist.linear.y == 0 && message_enu.twist.twist.linear.z == 0)) {
            return;
        }
        message_enu_previous_ = message_enu;
        {
            ros_bridge::ROSMsgCounter counter(&odom_pub_statistics);

            odom_pub.publish(message_enu);
        }
    }
    catch (rpc::rpc_error& e)
    {
        std::string msg = e.get_error().as<std::string>();
        ROS_ERROR_STREAM("Exception raised by the API while getting car state:" << std::endl << msg);
    }
}

void AirsimROSWrapper::gps_timer_cb(const ros::TimerEvent& event)
{
 try 
 {
    sensor_msgs::NavSatFix message;
    {
        ros_bridge::Timer timer(&getGpsDataStatistics);
        msr::airlib::GpsBase::Output gps_output = airsim_client_.getGpsData("Gps", vehicle_name);
        msr::airlib::GeoPoint gps_location = gps_output.gnss.geo_point;
        msr::airlib::GpsBase::GnssReport gnss_gps_report = gps_output.gnss;
        message = get_gps_sensor_msg_from_airsim_geo_point(gps_location);
        message.position_covariance[0] = gnss_gps_report.eph*gnss_gps_report.eph;
        message.position_covariance[4] = gnss_gps_report.eph*gnss_gps_report.eph;
        message.position_covariance[8] = gnss_gps_report.epv*gnss_gps_report.epv;
        message.header.stamp = AirsimROSWrapper::make_ts(gps_output.time_stamp);
    }
    {
        ros_bridge::ROSMsgCounter counter(&global_gps_pub_statistics);
        global_gps_pub.publish(message);
    }
 }
 catch (rpc::rpc_error& e)
 {
    std::string msg = e.get_error().as<std::string>();
    ROS_ERROR_STREAM("Exception raised by the API while getting gps data:" << std::endl << msg);
 }
}

void AirsimROSWrapper::imu_timer_cb(const ros::TimerEvent& event)
{
    try 
    {
        struct msr::airlib::ImuBase::Output imu_data;
        {
            ros_bridge::Timer timer(&getImuStatistics);
            std::unique_lock<std::recursive_mutex> lck(car_control_mutex_);
            imu_data = airsim_client_.getImuData("Imu", vehicle_name);
            lck.unlock();
        }

        sensor_msgs::Imu imu_msg = get_imu_msg_from_airsim(imu_data);
        imu_msg.angular_velocity_covariance[0] = imu_data.sigma_arw*imu_data.sigma_arw; 
        imu_msg.angular_velocity_covariance[4] = imu_data.sigma_arw*imu_data.sigma_arw;
        imu_msg.angular_velocity_covariance[8] = imu_data.sigma_arw*imu_data.sigma_arw;
        imu_msg.linear_acceleration_covariance[0] = imu_data.sigma_vrw*imu_data.sigma_vrw;
        imu_msg.linear_acceleration_covariance[4] = imu_data.sigma_vrw*imu_data.sigma_vrw;
        imu_msg.linear_acceleration_covariance[8] = imu_data.sigma_vrw*imu_data.sigma_vrw;
        imu_msg.header.frame_id = "fsds/" + vehicle_name;
        // imu_msg.header.stamp = ros::Time::now();
        {
            ros_bridge::ROSMsgCounter counter(&imu_pub_statistics);
            imu_pub.publish(imu_msg);
        }
    }
    catch (rpc::rpc_error& e)
    {
        std::string msg = e.get_error().as<std::string>();
        ROS_ERROR_STREAM("Exception raised by the API while getting imu data:" << std::endl << msg);
    }
}

void AirsimROSWrapper::gss_timer_cb(const ros::TimerEvent& event)
{
    try 
    {
        struct msr::airlib::GSSSimple::Output gss_data;
        {
            ros_bridge::Timer timer(&getGSSStatistics);
            std::unique_lock<std::recursive_mutex> lck(car_control_mutex_);
            gss_data = airsim_client_.getGroundSpeedSensorData(vehicle_name);
            lck.unlock();
        }

        geometry_msgs::TwistWithCovarianceStamped gss_msg;
        gss_msg.header.frame_id = "fsds/" + vehicle_name;
        gss_msg.header.stamp = make_ts(gss_data.time_stamp);

        gss_msg.twist.twist.angular.x = gss_data.angular_velocity.x();
        gss_msg.twist.twist.angular.y = gss_data.angular_velocity.y();
        gss_msg.twist.twist.angular.z = gss_data.angular_velocity.z();
        
        gss_msg.twist.twist.linear.x = gss_data.linear_velocity.x();
        gss_msg.twist.twist.linear.y = gss_data.linear_velocity.y();
        gss_msg.twist.twist.linear.z = gss_data.linear_velocity.z();

        // The 0.1 covariances for everything were just guessed, don't assume theese are correct
        gss_msg.twist.covariance[0] = 0.1;
        gss_msg.twist.covariance[7] = 0.1;
        gss_msg.twist.covariance[14] = 0.1;
        gss_msg.twist.covariance[21] = 0.1;
        gss_msg.twist.covariance[28] = 0.1;
        gss_msg.twist.covariance[35] = 0.1;

        {
            ros_bridge::ROSMsgCounter counter(&gss_pub_statistics);
            gss_pub.publish(gss_msg);
        }
    }
    catch (rpc::rpc_error& e)
    {
        std::string msg = e.get_error().as<std::string>();
        ROS_ERROR_STREAM("Exception raised by the API while getting gss data:" << std::endl << msg);
    }
}

void AirsimROSWrapper::statictf_cb(const ros::TimerEvent& event)
{
    for (auto& static_tf_msg : static_tf_msg_vec_)
    {
        static_tf_msg.header.stamp = ros::Time::now();
        static_tf_pub_.sendTransform(static_tf_msg);
    }
}


// airsim uses nans for zeros in settings.json. we set them to zeros here for handling tfs in ROS
void AirsimROSWrapper::set_nans_to_zeros_in_pose(VehicleSetting& vehicle_setting) const
{
    if (std::isnan(vehicle_setting.position.x()))
        vehicle_setting.position.x() = 0.0;

    if (std::isnan(vehicle_setting.position.y()))
        vehicle_setting.position.y() = 0.0;

    if (std::isnan(vehicle_setting.position.z()))
        vehicle_setting.position.z() = 0.0;

    if (std::isnan(vehicle_setting.rotation.yaw))
        vehicle_setting.rotation.yaw = 0.0;

    if (std::isnan(vehicle_setting.rotation.pitch))
        vehicle_setting.rotation.pitch = 0.0;

    if (std::isnan(vehicle_setting.rotation.roll))
        vehicle_setting.rotation.roll = 0.0;
}

// if any nan's in camera pose, set them to match vehicle pose (which has already converted any potential nans to zeros)
void AirsimROSWrapper::set_nans_to_zeros_in_pose(const VehicleSetting& vehicle_setting, CameraSetting& camera_setting) const
{
    if (std::isnan(camera_setting.position.x()))
        camera_setting.position.x() = vehicle_setting.position.x();

    if (std::isnan(camera_setting.position.y()))
        camera_setting.position.y() = vehicle_setting.position.y();

    if (std::isnan(camera_setting.position.z()))
        camera_setting.position.z() = vehicle_setting.position.z();

    if (std::isnan(camera_setting.rotation.yaw))
        camera_setting.rotation.yaw = vehicle_setting.rotation.yaw;

    if (std::isnan(camera_setting.rotation.pitch))
        camera_setting.rotation.pitch = vehicle_setting.rotation.pitch;

    if (std::isnan(camera_setting.rotation.roll))
        camera_setting.rotation.roll = vehicle_setting.rotation.roll;
}

void AirsimROSWrapper::set_nans_to_zeros_in_pose(const VehicleSetting& vehicle_setting, LidarSetting& lidar_setting) const
{
    if (std::isnan(lidar_setting.position.x()))
        lidar_setting.position.x() = vehicle_setting.position.x();

    if (std::isnan(lidar_setting.position.y()))
        lidar_setting.position.y() = vehicle_setting.position.y();

    if (std::isnan(lidar_setting.position.z()))
        lidar_setting.position.z() = vehicle_setting.position.z();

    if (std::isnan(lidar_setting.rotation.yaw))
        lidar_setting.rotation.yaw = vehicle_setting.rotation.yaw;

    if (std::isnan(lidar_setting.rotation.pitch))
        lidar_setting.rotation.pitch = vehicle_setting.rotation.pitch;

    if (std::isnan(lidar_setting.rotation.roll))
        lidar_setting.rotation.roll = vehicle_setting.rotation.roll;
}

void AirsimROSWrapper::append_static_lidar_tf(const std::string& vehicle_name, const std::string& lidar_name, const LidarSetting& lidar_setting)
{

    geometry_msgs::TransformStamped lidar_tf_msg;
    lidar_tf_msg.header.frame_id = "fsds/" + vehicle_name;
    lidar_tf_msg.child_frame_id = "fsds/" + lidar_name;
    lidar_tf_msg.transform.translation.x = lidar_setting.position.x();
    lidar_tf_msg.transform.translation.y = lidar_setting.position.y();
    lidar_tf_msg.transform.translation.z = lidar_setting.position.z();
    tf2::Quaternion quat;
    quat.setRPY(math_common::deg2rad(lidar_setting.rotation.roll), math_common::deg2rad(lidar_setting.rotation.pitch), math_common::deg2rad(lidar_setting.rotation.yaw));
    lidar_tf_msg.transform.rotation.x = quat.x();
    lidar_tf_msg.transform.rotation.y = quat.y();
    lidar_tf_msg.transform.rotation.z = quat.z();
    lidar_tf_msg.transform.rotation.w = quat.w();

    static_tf_msg_vec_.push_back(lidar_tf_msg);
}

void AirsimROSWrapper::append_static_camera_tf(const std::string& vehicle_name, const std::string& camera_name, const CameraSetting& camera_setting)
{
    geometry_msgs::TransformStamped static_cam_tf_body_msg;
    static_cam_tf_body_msg.header.frame_id = "fsds/" + vehicle_name;
    static_cam_tf_body_msg.child_frame_id = "fsds/" + camera_name;
    static_cam_tf_body_msg.transform.translation.x = camera_setting.position.x();
    static_cam_tf_body_msg.transform.translation.y = camera_setting.position.y();
    static_cam_tf_body_msg.transform.translation.z = camera_setting.position.z();
    tf2::Quaternion quat;
    quat.setRPY(math_common::deg2rad(camera_setting.rotation.roll), math_common::deg2rad(camera_setting.rotation.pitch), math_common::deg2rad(camera_setting.rotation.yaw));
    static_cam_tf_body_msg.transform.rotation.x = quat.x();
    static_cam_tf_body_msg.transform.rotation.y = quat.y();
    static_cam_tf_body_msg.transform.rotation.z = quat.z();
    static_cam_tf_body_msg.transform.rotation.w = quat.w();

    static_tf_msg_vec_.push_back(static_cam_tf_body_msg);
}

void AirsimROSWrapper::lidar_timer_cb(const ros::TimerEvent& event, const std::string& lidar_name, const int lidar_index)
{
    try
    {
        sensor_msgs::PointCloud2 lidar_msg;
        struct msr::airlib::LidarData lidar_data;
        {
            ros_bridge::Timer timer(&getLidarDataVecStatistics[lidar_index]);
            std::unique_lock<std::recursive_mutex> lck(car_control_mutex_);
            lidar_data = airsim_client_lidar_.getLidarData(lidar_name, vehicle_name); // airsim api is imu_name, vehicle_name
            lck.unlock();
        }
        lidar_msg = get_lidar_msg_from_airsim(lidar_name, lidar_data);     // todo make const ptr msg to avoid copy
        lidar_msg.header.frame_id = "fsds/" + lidar_name;
        lidar_msg.header.stamp = ros::Time::now();

        {
            ros_bridge::ROSMsgCounter counter(&lidar_pub_vec_statistics[lidar_index]);
            lidar_pub_vec_[lidar_index].publish(lidar_msg);
        }
    }

    catch (rpc::rpc_error& e)
    {
        std::string msg = e.get_error().as<std::string>();
        ROS_ERROR_STREAM("Exception raised by the API, didn't get lidar response." << std::endl << msg);
    }
}

/* 
    STATISTICS
 */

// TODO: it would be nice to avoid code duplication between Print and Reset
// functions with templates or something similar
void AirsimROSWrapper::PrintStatistics()
{
    // This did not work for some reason
    // for (auto statistics_obj : statistics_obj_ptr)
    // {
    //     statistics_obj->Print();
    // }
    std::stringstream dbg_msg;
    dbg_msg << "--------- ros_wrapper statistics ---------" << std::endl;
    dbg_msg << setCarControlsStatistics.getSummaryAsString() << std::endl;

    if(enabled_sensors.gps){
        dbg_msg << getGpsDataStatistics.getSummaryAsString() << std::endl;
        dbg_msg << global_gps_pub_statistics.getSummaryAsString() << std::endl;
    }

    dbg_msg << getCarStateStatistics.getSummaryAsString() << std::endl;

    if(enabled_sensors.imu){
        dbg_msg << getImuStatistics.getSummaryAsString() << std::endl;
        dbg_msg << imu_pub_statistics.getSummaryAsString() << std::endl;
    }

    if(enabled_sensors.gss){
        dbg_msg << getGSSStatistics.getSummaryAsString() << std::endl;
        dbg_msg << gss_pub_statistics.getSummaryAsString() << std::endl;
    }

    dbg_msg << control_cmd_sub_statistics.getSummaryAsString() << std::endl;
    dbg_msg << odom_pub_statistics.getSummaryAsString() << std::endl;

    for (auto &getLidarDataStatistics : getLidarDataVecStatistics)
    {
        dbg_msg << getLidarDataStatistics.getSummaryAsString() << std::endl;
    }

    // Reset lidar statistics
    for (auto &lidar_pub_statistics : lidar_pub_vec_statistics)
    {
        dbg_msg << lidar_pub_statistics.getSummaryAsString() << std::endl;
    }
    dbg_msg << "------------------------------------------" << std::endl;
    ROS_DEBUG( dbg_msg.str().c_str());
}

void AirsimROSWrapper::ResetStatistics()
{
    // This did not work for some reason
    // for (auto statistics_obj : statistics_obj_ptr)
    // {
    //     statistics_obj->Reset();
    // }
    setCarControlsStatistics.Reset();

    if(enabled_sensors.gps){
        getGpsDataStatistics.Reset();
        global_gps_pub_statistics.Reset();
    }
    getCarStateStatistics.Reset();

    if(enabled_sensors.imu){
        getImuStatistics.Reset();
        imu_pub_statistics.Reset();
    }

    if(enabled_sensors.gss){
        getGSSStatistics.Reset();
        gss_pub_statistics.Reset();
    }

    control_cmd_sub_statistics.Reset();
    odom_pub_statistics.Reset();

    for (auto &getLidarDataStatistics : getLidarDataVecStatistics)
    {
        getLidarDataStatistics.Reset();
    }

    // Reset lidar statistics
    for (auto &lidar_pub_statistics : lidar_pub_vec_statistics)
    {
        lidar_pub_statistics.Reset();
    }
}

// This callback is executed every 1 second
void AirsimROSWrapper::statistics_timer_cb(const ros::TimerEvent &event)
{
    // The lines below are technically correct but for some reason they introduce a lot of noise in the data, which is exactly what they are not supposed to do
    // long double time_elapsed = event.current_real.nsec - event.last_real.nsec; // nanoseconds for accuracy
    // ros_bridge::Statistics::SetTimeElapsed((double)(time_elapsed*std::pow(10, -9))); // convert back to seconds
    PrintStatistics();
    ResetStatistics();
}

// This callback is executed every 1 second
void AirsimROSWrapper::go_signal_timer_cb(const ros::TimerEvent &event)
{
    fs_msgs::GoSignal go_signal_msg;
    go_signal_msg.header.stamp = go_timestamp_;
    go_signal_msg.mission = mission_name_;
    go_signal_msg.track = track_name_;
    go_signal_pub_.publish(go_signal_msg);
}

void AirsimROSWrapper::finished_signal_cb(fs_msgs::FinishedSignalConstPtr msg)
{
    // Get access token
    std::string operator_token(std::getenv("OPERATOR_TOKEN"));
    std::string operator_url(std::getenv("OPERATOR_URL"));
    operator_url = operator_url + "/finished";

    std::cout << operator_token << std::endl;
    std::cout << operator_url << std::endl;

    ROS_DEBUG_STREAM("Operator token: " << operator_token.c_str() << " operator url: " << operator_url.c_str());

    // Send JSON HTTP POST request
    CURL *curl;
    CURLcode res;

    curl_global_init(CURL_GLOBAL_ALL);
    curl = curl_easy_init();

    std::string json_obj = "{\"access_token\" : \"" + operator_token + "\"}";

    struct curl_slist *headers = NULL;
    headers = curl_slist_append(headers, "Accept: application/json");
    headers = curl_slist_append(headers, "Content-Type: application/json");
    headers = curl_slist_append(headers, "charsets: utf-8");

    curl_easy_setopt(curl, CURLOPT_URL, operator_url.c_str());
    curl_easy_setopt(curl, CURLOPT_CUSTOMREQUEST, "POST");
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_obj.c_str());

    res = curl_easy_perform(curl);
    ROS_DEBUG_STREAM("curl_easy_perform() returned: " << res);


    curl_easy_cleanup(curl);
    curl_global_cleanup();
}

void AirsimROSWrapper::extra_info_cb(const ros::TimerEvent & event){
	CarApiBase::RefereeState state;
    try{
        std::unique_lock<std::recursive_mutex> lck(car_control_mutex_);
        state = airsim_client_.getRefereeState();
        lck.unlock();
    } catch (rpc::rpc_error& e)
    {
        std::string msg = e.get_error().as<std::string>();
        ROS_ERROR_STREAM("Exception raised by the API, something went wrong while retrieving referee state for sending extra info." << std::endl << msg);
    }

	fs_msgs::ExtraInfo extra_info_msg;
	extra_info_msg.doo_counter = state.doo_counter;
	extra_info_msg.laps = state.laps;

	extra_info_pub.publish(extra_info_msg);
}

bool AirsimROSWrapper::equalsMessage(const nav_msgs::Odometry& a, const nav_msgs::Odometry& b) {
    return a.pose.pose.position.x == b.pose.pose.position.x &&
        a.pose.pose.position.y == b.pose.pose.position.y &&
        a.pose.pose.position.z == b.pose.pose.position.z &&
        a.pose.pose.orientation.x == b.pose.pose.orientation.x &&
        a.pose.pose.orientation.y == b.pose.pose.orientation.y &&
        a.pose.pose.orientation.z == b.pose.pose.orientation.z &&
        a.pose.pose.orientation.w == b.pose.pose.orientation.w &&
        a.twist.twist.linear.x == b.twist.twist.linear.x &&
        a.twist.twist.linear.y == b.twist.twist.linear.y &&
        a.twist.twist.linear.z == b.twist.twist.linear.z &&
        a.twist.twist.angular.x == b.twist.twist.angular.x &&
        a.twist.twist.angular.y == b.twist.twist.angular.y &&
        a.twist.twist.angular.z == b.twist.twist.angular.z;
}

std::string AirsimROSWrapper::readTextFromFile(std::string settingsFilepath) 	
{	
    // check if path exists	
    if(!std::ifstream(settingsFilepath.c_str()).good()){
        throw std::invalid_argument("settings.json file does not exist. Ensure the ~/Formula-Student-Driverless-Simulator/settings.json file exists.");
    }
    std::ifstream ifs(settingsFilepath);	
    std::stringstream buffer;	
    buffer << ifs.rdbuf();		
    return buffer.str();
}
