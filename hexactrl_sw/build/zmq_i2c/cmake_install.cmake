# Install script for directory: /home/HGCAL_dev/sw/hexactrl-sw/zmq_i2c

# Set the install prefix
IF(NOT DEFINED CMAKE_INSTALL_PREFIX)
  SET(CMAKE_INSTALL_PREFIX "/usr/local")
ENDIF(NOT DEFINED CMAKE_INSTALL_PREFIX)
STRING(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
IF(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  IF(BUILD_TYPE)
    STRING(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  ELSE(BUILD_TYPE)
    SET(CMAKE_INSTALL_CONFIG_NAME "")
  ENDIF(BUILD_TYPE)
  MESSAGE(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
ENDIF(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)

# Set the component getting installed.
IF(NOT CMAKE_INSTALL_COMPONENT)
  IF(COMPONENT)
    MESSAGE(STATUS "Install component: \"${COMPONENT}\"")
    SET(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  ELSE(COMPONENT)
    SET(CMAKE_INSTALL_COMPONENT)
  ENDIF(COMPONENT)
ENDIF(NOT CMAKE_INSTALL_COMPONENT)

# Install shared libraries without execute permission?
IF(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  SET(CMAKE_INSTALL_SO_NO_EXE "0")
ENDIF(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)

IF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "Unspecified")
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/opt/hexactrl/ROCv3/etc/HGCROCv2_I2C_params_regmap_dict.pickle;/opt/hexactrl/ROCv3/etc/HGCROC3_I2C_params_regmap_dict.pickle;/opt/hexactrl/ROCv3/etc/HGCROCv2_sipm_I2C_params_regmap_dict.pickle;/opt/hexactrl/ROCv3/etc/HGCROC3_sipm_I2C_params_regmap_dict.pickle")
  IF (CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  ENDIF (CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
  IF (CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  ENDIF (CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
FILE(INSTALL DESTINATION "/opt/hexactrl/ROCv3/etc" TYPE FILE FILES
    "/home/HGCAL_dev/sw/hexactrl-sw/zmq_i2c/reg_maps/HGCROCv2_I2C_params_regmap_dict.pickle"
    "/home/HGCAL_dev/sw/hexactrl-sw/zmq_i2c/reg_maps/HGCROC3_I2C_params_regmap_dict.pickle"
    "/home/HGCAL_dev/sw/hexactrl-sw/zmq_i2c/reg_maps/HGCROCv2_sipm_I2C_params_regmap_dict.pickle"
    "/home/HGCAL_dev/sw/hexactrl-sw/zmq_i2c/reg_maps/HGCROC3_sipm_I2C_params_regmap_dict.pickle"
    )
ENDIF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "Unspecified")

IF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "Unspecified")
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/opt/hexactrl/ROCv3/etc/requirements.txt")
  IF (CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  ENDIF (CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
  IF (CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  ENDIF (CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
FILE(INSTALL DESTINATION "/opt/hexactrl/ROCv3/etc" TYPE FILE FILES "/home/HGCAL_dev/sw/hexactrl-sw/zmq_i2c/requirements.txt")
ENDIF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "Unspecified")

IF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "Unspecified")
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/opt/hexactrl/ROCv3/i2c/Boards.py;/opt/hexactrl/ROCv3/i2c/Link.py;/opt/hexactrl/ROCv3/i2c/ROC.py;/opt/hexactrl/ROCv3/i2c/Translator.py;/opt/hexactrl/ROCv3/i2c/zmq_server.py;/opt/hexactrl/ROCv3/i2c/configure.py")
  IF (CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  ENDIF (CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
  IF (CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  ENDIF (CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
FILE(INSTALL DESTINATION "/opt/hexactrl/ROCv3/i2c" TYPE FILE FILES
    "/home/HGCAL_dev/sw/hexactrl-sw/zmq_i2c/Boards.py"
    "/home/HGCAL_dev/sw/hexactrl-sw/zmq_i2c/Link.py"
    "/home/HGCAL_dev/sw/hexactrl-sw/zmq_i2c/ROC.py"
    "/home/HGCAL_dev/sw/hexactrl-sw/zmq_i2c/Translator.py"
    "/home/HGCAL_dev/sw/hexactrl-sw/zmq_i2c/zmq_server.py"
    "/home/HGCAL_dev/sw/hexactrl-sw/zmq_i2c/configure.py"
    )
ENDIF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "Unspecified")

