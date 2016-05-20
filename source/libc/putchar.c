/*
 * Copyright (C) 2016 Kubos Corporation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
/**
  * @defgroup libc
  * @addtogroup libc
  * @{
  */

/**
  *
  * @file       putchar.c
  * @brief      Kubos-HAL-MSP430F5529 - putchar
  *
  * @author     kubos.co
  */
 #include "kubos-hal/uart.h"

/**
  * @brief uart putchar implementation using default console
  */
int putchar(int c)
{
    return k_uart_write(K_UART_CONSOLE, &c, 1);
}
