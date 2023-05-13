/*
 Navicat Premium Data Transfer

 Source Server         : 阿里云
 Source Server Type    : MySQL
 Source Server Version : 80027
 Source Host           : 8.142.109.254:3306
 Source Schema         : ry

 Target Server Type    : MySQL
 Target Server Version : 80027
 File Encoding         : 65001

 Date: 13/05/2023 18:00:06
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for shooter_score
-- ----------------------------
DROP TABLE IF EXISTS `shooter_score`;
CREATE TABLE `shooter_score`  (
  `uuid` varchar(32) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT 'uuid',
  `name` varchar(10) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '名字',
  `number` int NULL DEFAULT NULL COMMENT '编号',
  `time` datetime NULL DEFAULT NULL COMMENT '时间',
  `score` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT '成绩',
  `hitRingNumber` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT '命中环数',
  `aimRingNumber` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT '瞄准环数',
  `gunShaking` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT '据枪晃动量',
  `gunShakingRate` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT '据枪晃动速率',
  `fireShaking` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT '击发晃动量',
  `fireShakingRate` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT '击发晃动速率',
  `shootingAccuracy` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT '射击精确性',
  `gunStability` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT '据枪稳定性',
  `firingStability` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT '击发稳定性',
  PRIMARY KEY (`uuid`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
