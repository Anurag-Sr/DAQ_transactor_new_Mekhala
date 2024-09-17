cmake_minimum_required(VERSION 2.6 FATAL_ERROR)
project( hexactrl )

include(CheckCXXCompilerFlag)
check_cxx_compiler_flag(-std=c++14 HAVE_FLAG_STD_CXX14)
if(HAVE_FLAG_STD_CXX14)
  set( CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++14" )
  message("will use c++14")
else()
  check_cxx_compiler_flag(-std=c++11 HAVE_FLAG_STD_CXX11)
  if(HAVE_FLAG_STD_CXX11)
    set( CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11" )
    message("will use c++11")
  else()
    message( FATAL_ERROR "C++ 11 or higher is required")
  endif()
endif()

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}  -lzmq -lyaml-cpp -Wall -fPIC -O3")

find_package(Git)
if(GIT_FOUND)
  message("Git found ${GIT_EXECUTABLE}  ${GIT_VERSION_STRING} ")
endif()

if(NOT DEFINED BRANCH_NAME)
  execute_process(
    COMMAND ${GIT_EXECUTABLE} rev-parse --abbrev-ref HEAD
    WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR}
    OUTPUT_VARIABLE BRANCH_NAME
    OUTPUT_STRIP_TRAILING_WHITESPACE
    )
endif()
message("DEFINE BRANCH_NAME ${BRANCH_NAME}")

execute_process(
  COMMAND git log -1 --format=%h
  WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR}
  OUTPUT_VARIABLE GIT_HASH
  OUTPUT_STRIP_TRAILING_WHITESPACE
  )
set(DESTINATION "/opt/hexactrl/${BRANCH_NAME}")

option( BUILD_CLIENT "Build and compile client tools" OFF )
option( MONGOOSE_WEB_TOOL "Build and compile mongoose tool" OFF )

list(APPEND CMAKE_PREFIX_PATH $ENV{ROOTSYS})
list( APPEND CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR}/cmake )

find_package( Boost COMPONENTS thread system filesystem timer REQUIRED )

include_directories( SYSTEM ${CMAKE_CURRENT_SOURCE_DIR}/sources/common/include ${Boost_INCLUDE_DIRS} )
link_directories( ${EXTERN_BOOST_LIB_PREFIX} )

file( GLOB sources ${PROJECT_SOURCE_DIR}/sources/common/src/*.cc )
file( GLOB headers ${PROJECT_SOURCE_DIR}/sources/common/include/*.h )

if( NOT BUILD_CLIENT )
  install(FILES ${PROJECT_SOURCE_DIR}/address_table/connection.xml DESTINATION ${DESTINATION}/etc)
  install(FILES ${PROJECT_SOURCE_DIR}/env.sh DESTINATION ${DESTINATION}/etc)
  add_subdirectory(zmq_i2c)

  find_package( CACTUS REQUIRED )
  include_directories( ${CMAKE_CURRENT_SOURCE_DIR}/sources/server/include  ${UHAL_LOG_INCLUDE_PREFIX} ${UHAL_GRAMMARS_INCLUDE_PREFIX} ${UHAL_UHAL_INCLUDE_PREFIX})
  link_directories( ${link_directories} ${UHAL_LOG_LIB_PREFIX} ${UHAL_GRAMMARS_LIB_PREFIX} ${UHAL_UHAL_LIB_PREFIX} )
  file( GLOB sources ${sources} ${PROJECT_SOURCE_DIR}/sources/server/src/*.cc )
  file( GLOB headers ${headers} ${PROJECT_SOURCE_DIR}/sources/server/include/*.h )
  file( GLOB executables ${PROJECT_SOURCE_DIR}/sources/server/executables/*.cxx )

  add_library(objectlib OBJECT ${sources})
  message( "-- Server executables to be installed")
  foreach( exec ${executables} )
    message( "\t${exec}" )
    get_filename_component(ex ${exec} NAME_WE)
    add_executable( ${ex} ${exec} $<TARGET_OBJECTS:objectlib> ${headers} )
    target_link_libraries( ${ex} ${Boost_LIBRARIES} boost_program_options boost_regex boost_serialization boost_chrono cactus_uhal_log cactus_uhal_grammars cactus_uhal_uhal )
    install( TARGETS ${ex} DESTINATION ${DESTINATION}/bin
      ARCHIVE DESTINATION ${DESTINATION}/lib
      LIBRARY DESTINATION ${DESTINATION}/lib )
  endforeach()

  add_library( ${PROJECT_NAME} SHARED ${sources} )
  target_link_libraries( ${PROJECT_NAME} ${Boost_LIBRARIES} boost_program_options boost_regex boost_serialization boost_chrono cactus_uhal_log cactus_uhal_grammars cactus_uhal_uhal )
  target_include_directories( ${PROJECT_NAME} PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include )
  install( TARGETS ${PROJECT_NAME}
    ARCHIVE DESTINATION ${DESTINATION}/lib
    LIBRARY DESTINATION ${DESTINATION}/lib )

  set(SERVICE_NAMES i2c-server.service daq-server.service )
  message( "${SERVICE_NAMES}" )
  set(SER_EXE_PATH ${DESTINATION}/bin/daq-server)
  set(SER_XML_PATH ${DESTINATION}/etc/connection.xml)
  set(SER_ENV_PATH ${DESTINATION}/etc/env.sh)
  set(SER_I2C_PATH ${DESTINATION}/i2c/zmq_server.py)

  # unset(SERVICE_NAME)
  # set(SERVICE_NAME i2c-server.service )
  # set(SERVICE_IN ${CMAKE_CURRENT_SOURCE_DIR}/services/${SERVICE_NAME}.in)
  # set(SERVICE_OUT ${CMAKE_CURRENT_BINARY_DIR}/${SERVICE_NAME})
  # configure_file(${SERVICE_IN} ${SERVICE_OUT} @ONLY)
  # install(FILES ${SERVICE_OUT} DESTINATION ${DESTINATION}/share)
  
else()
  add_subdirectory(hexactrl-script)
  find_package( ROOT REQUIRED ) 
  if( ROOT_FOUND )
    include_directories( ${ROOT_INCLUDE_DIRS} )
    link_libraries( ${ROOT_LIBRARIES} )
    add_definitions( ${ROOT_DEFINITIONS} )
  endif()
  include_directories( ${CMAKE_CURRENT_SOURCE_DIR}/sources/client/include )
  file( GLOB sources ${sources} ${PROJECT_SOURCE_DIR}/sources/client/src/*.cc )
  file( GLOB headers ${headers} ${PROJECT_SOURCE_DIR}/sources/client/include/*.h )
  file( GLOB executables ${PROJECT_SOURCE_DIR}/sources/client/executables/*.cxx )
  message( "-- Client executables to be installed")
  add_library(anaobjectlib OBJECT ${sources})
  foreach( exec ${executables} )
    message( "\t${exec}" )
    get_filename_component(ex ${exec} NAME_WE)
    add_executable( ${ex} ${exec} $<TARGET_OBJECTS:anaobjectlib> ${headers} )
    target_link_libraries( ${ex} ${Boost_LIBRARIES} boost_program_options boost_regex boost_serialization boost_chrono )
    install( TARGETS ${ex} DESTINATION ${DESTINATION}/bin
      ARCHIVE DESTINATION ${DESTINATION}/lib
      LIBRARY DESTINATION ${DESTINATION}/lib )
  endforeach()

  set(SERVICE_NAMES daq-client.service) 
  set(CLI_EXE_PATH ${DESTINATION}/bin/daq-client)
  # set(SERVICE_IN ${CMAKE_CURRENT_SOURCE_DIR}/services/${SERVICE_NAME}.in)
  # set(SERVICE_OUT ${CMAKE_CURRENT_BINARY_DIR}/${SERVICE_NAME})
  # configure_file(${SERVICE_IN} ${SERVICE_OUT} @ONLY)
  # install(FILES ${SERVICE_OUT} DESTINATION ${DESTINATION}/share)
  
endif(  )

if( MONGOOSE_WEB_TOOL )
  find_package( Mongoose REQUIRED )
  include_directories( ${CMAKE_CURRENT_SOURCE_DIR}/sources/mongoose_web_tool/include )
  file( GLOB sources ${sources} ${PROJECT_SOURCE_DIR}/sources/mongoose_web_tool/src/*.cc )
  file( GLOB headers ${headers} ${PROJECT_SOURCE_DIR}/sources/mongoose_web_tool/include/*.h )
  file( GLOB mongoose_executables ${PROJECT_SOURCE_DIR}/sources/mongoose_web_tool/executables/*.cxx )
  message( "-- Mongoose web tool executables to be installed")
  foreach( exec ${mongoose_executables} )
    message( "\t${exec}" )
    get_filename_component(ex ${exec} NAME_WE)
    add_executable( ${ex} ${exec} ${sources} ${headers} )
    target_link_libraries( ${ex} ${Boost_LIBRARIES} boost_program_options boost_regex boost_serialization boost_chrono cactus_uhal_log cactus_uhal_grammars cactus_uhal_uhal mongoose )
    install( TARGETS ${ex} DESTINATION ${DESTINATION}/bin
      ARCHIVE DESTINATION ${DESTINATION}/lib
      LIBRARY DESTINATION ${DESTINATION}/lib )
  endforeach()
endif( MONGOOSE_WEB_TOOL )

string(TIMESTAMP TODAY "%Y.%m.%d.%H.%M.%S")

find_package(PythonInterp 3 REQUIRED)
include(FindPythonInterp)
set(PYTHON ${PYTHON_EXECUTABLE})
message(STATUS "\${PYTHON_EXECUTABLE} == ${PYTHON_EXECUTABLE}")

set(CPACK_RPM_BUILDREQUIRES python3-devel)
set(CPACK_RPM_SPEC_MORE_DEFINE "%define __python ${PYTHON_EXECUTABLE}")

set(CPACK_PACKAGE_VERSION ${TODAY})
set(CPACK_GENERATOR "RPM")
set(CPACK_PACKAGE_NAME "hexactrl-sw-${BRANCH_NAME}")
# set(CPACK_PACKAGE_RELEASE 1)
set(CPACK_PACKAGE_CONTACT "asteen")
set(CPACK_PACKAGE_VENDOR "hgcal")
set(CPACK_PACKAGING_INSTALL_PREFIX ${CMAKE_INSTALL_PREFIX})
set(CPACK_PACKAGE_FILE_NAME "${CPACK_PACKAGE_NAME}-${TODAY}-${GIT_HASH}.${CMAKE_SYSTEM_PROCESSOR}")


foreach( SERVICE_NAME ${SERVICE_NAMES} )
  set(SERVICE_IN ${CMAKE_CURRENT_SOURCE_DIR}/services/${SERVICE_NAME}.in)
  set(SERVICE_OUT ${CMAKE_CURRENT_BINARY_DIR}/${SERVICE_NAME})
  configure_file(${SERVICE_IN} ${SERVICE_OUT} @ONLY)
  install(FILES ${SERVICE_OUT} DESTINATION ${DESTINATION}/share)
endforeach()

set(VERBOSE_LOGGING FALSE)
set(POST_IN ${CMAKE_CURRENT_LIST_DIR}/services/post.sh.in)
set(POST_OUT ${CMAKE_CURRENT_BINARY_DIR}/post.sh)
configure_file(${POST_IN} ${POST_OUT} @ONLY)
set(POSTUN_IN ${CMAKE_CURRENT_LIST_DIR}/services/postun.sh.in)
set(POSTUN_OUT ${CMAKE_CURRENT_BINARY_DIR}/postun.sh)
configure_file(${POSTUN_IN} ${POSTUN_OUT} @ONLY)
set(PREUN_IN ${CMAKE_CURRENT_LIST_DIR}/services/preun.sh.in)
set(PREUN_OUT ${CMAKE_CURRENT_BINARY_DIR}/preun.sh)
configure_file(${PREUN_IN} ${PREUN_OUT} @ONLY)

set(CPACK_RPM_POST_INSTALL_SCRIPT_FILE ${POST_OUT})
set(CPACK_RPM_POST_UNINSTALL_SCRIPT_FILE ${POSTUN_OUT})
set(CPACK_RPM_PRE_UNINSTALL_SCRIPT_FILE ${PREUN_OUT})

set(CPACK_RPM_PACKAGE_REQUIRES_POSTUN "systemd")
set(CPACK_RPM_PACKAGE_REQUIRES_PREUN "systemd")
set(CPACK_RPM_PACKAGE_REQUIRES_POST "systemd")

include(CPack)
